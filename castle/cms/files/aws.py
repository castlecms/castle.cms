import io
import logging
import math
import urllib
from datetime import datetime
from time import time
from urlparse import urlparse

from boto.s3.connection import (ProtocolIndependentOrdinaryCallingFormat,
                                S3Connection)
from collective.celery.utils import getCelery
from persistent.mapping import PersistentMapping
from plone.namedfile.file import NamedBlobFile
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility


logger = logging.getLogger('castle.cms')


CHUNK_SIZE = 12428800
STORAGE_KEY = 'castle.cms.aws'
FILENAME = u'moved-to-s3'
EXPIRES_IN = 30 * 24 * 60 * 60

# define prefix for keys on where to store data in aws
KEY_PREFIX = 'files/'


def get_bucket(s3_bucket=None):
    registry = getUtility(IRegistry)
    s3_id = registry.get('castle.aws_s3_key', None)
    s3_key = registry.get('castle.aws_s3_secret', None)
    if s3_bucket is None:
        s3_bucket = registry.get('castle.aws_s3_bucket_name', None)

    if not s3_id or not s3_key or not s3_bucket:
        return None, None

    endpoint = registry.get('castle.aws_s3_host_endpoint', None)
    if endpoint:
        s3_conn = S3Connection(
            s3_id, s3_key, host=endpoint,
            calling_format=ProtocolIndependentOrdinaryCallingFormat())
    else:
        s3_conn = S3Connection(s3_id, s3_key)

    return s3_conn, s3_conn.get_bucket(s3_bucket)


def move_file(obj):
    _, bucket = get_bucket()
    if bucket is None:
        return

    uid = IUUID(obj)
    if not uid:
        logger.info('Could not get uid of object')
        return

    key = KEY_PREFIX + uid
    filename = obj.file.filename
    if not isinstance(filename, unicode):
        filename = unicode(filename, 'utf-8', errors="ignore")
    filename = urllib.quote(filename.encode("utf8"))
    disposition = "attachment; filename*=UTF-8''%s" % filename

    size = obj.file.getSize()
    chunk_count = int(math.ceil(size / float(CHUNK_SIZE)))
    content_type = obj.file.contentType
    mp = bucket.initiate_multipart_upload(key, metadata={
        'Content-Type': content_type,
        'Content-Disposition': disposition
    })

    blob_fi = obj.file._blob.open('r')

    for i in range(chunk_count):
        chunk = blob_fi.read(CHUNK_SIZE)
        fp = io.BytesIO(chunk)
        mp.upload_part_from_file(fp, part_num=i + 1)

    mp.complete_upload()
    blob_fi.close()

    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    obj.file = NamedBlobFile(data='', contentType=obj.file.contentType, filename=FILENAME)
    obj.file.original_filename = filename
    obj.file.original_content_type = content_type
    obj.file.original_size = size

    set_permission(obj)


def set_permission(obj):
    s3_conn, bucket = get_bucket()
    if bucket is None:
        return
    uid = IUUID(obj)
    key_name = KEY_PREFIX + uid
    key = bucket.get_key(key_name)
    if key is None:
        return

    perms = obj.rolesOfPermission("View")
    public = False
    for perm in perms:
        if perm["name"] == "Anonymous":
            if perm["selected"] != "":
                public = True
                break

    annotations = IAnnotations(obj)
    info = annotations.get(STORAGE_KEY, PersistentMapping())
    if public:
        key.make_public()
        expires_in = 0
        url = 'https://{host}/{bucket}/{key}'.format(
            host=s3_conn.server_name(),
            bucket=bucket.name,
            key=key_name)
    else:
        key.set_canned_acl('private')
        url = key.generate_url(EXPIRES_IN)
        expires_in = EXPIRES_IN

    info.update({
        'url': url,
        'expires_in': expires_in,
        'generated_on': time()
    })
    annotations[STORAGE_KEY] = info


def delete_file(uid):
    _, bucket = get_bucket()
    if bucket is None:
        return

    key_name = KEY_PREFIX + uid
    key = bucket.get_key(key_name)
    if key:
        bucket.delete_key(key_name)


def uploaded(obj):
    try:
        annotations = IAnnotations(obj)
    except TypeError:
        return False
    info = annotations.get(STORAGE_KEY, PersistentMapping())
    return 'url' in info


def _one(val):
    """Wonky, values returning tuple sometimes?"""
    if type(val) in (tuple, list, set):
        if len(val) > 0:
            val = val[0]
        else:
            return
    return val


def swap_url(url, registry=None, base_url=None):
    """
    aws url: https://s3-us-gov-west-1.amazonaws.com/bucketname/archives/path/to/resource
    base url: http://foo.com/
    swapped: http://foo.com/archives/path/to/resource
    """
    if base_url is None:
        if registry is None:
            registry = getUtility(IRegistry)
        base_url = registry.get('castle.aws_s3_base_url', None)

    if base_url:
        parsed_url = urlparse(url)
        url = '{}/{}'.format(base_url.strip('/'), '/'.join(parsed_url.path.split('/')[2:]))
        if parsed_url.query:
            url += '?' + parsed_url.query
    return url


def get_url(obj):
    annotations = IAnnotations(obj)
    info = annotations.get(STORAGE_KEY, PersistentMapping())

    if info['expires_in'] != 0:
        # not public, check validity of url
        generated_on = info['generated_on']
        expires = datetime.fromtimestamp(generated_on + info['expires_in'])
        if datetime.utcnow() > expires:
            # need a new url
            _, bucket = get_bucket()
            uid = IUUID(obj)
            key = bucket.get_key(KEY_PREFIX + uid)
            url = key.generate_url(EXPIRES_IN)
            info.update({
                'url': url,
                'generated_on': time(),
                'expires_in': EXPIRES_IN
            })
            annotations[STORAGE_KEY] = info
    url = _one(info['url'])
    if not url.startswith('http'):
        url = 'https:' + url

    return swap_url(url)
