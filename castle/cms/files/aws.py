# for compat with python3, specifically the urllib.parse includes
# noqa because these need to precede other imports
from future.standard_library import install_aliases
install_aliases()  # noqa

import logging
from datetime import datetime
import StringIO
from time import time
from urllib.parse import urlsplit, urlunsplit, quote, quote_plus

import botocore
import boto3
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

    s3args = {
        'aws_access_key_id': s3_id,
        'aws_secret_access_key': s3_key,
    }

    endpoint = registry.get('castle.aws_s3_host_endpoint', None)
    if endpoint:
        s3args['endpoint_url'] = endpoint

    s3 = boto3.resource('s3', **s3args)
    bucket = None
    try:
        s3.meta.client.head_bucket(Bucket=s3_bucket)
        bucket = s3.Bucket(s3_bucket)
    except botocore.exceptions.ClientError as e:
        bucket = None
        error_code = e.response['Error']['Code']
        if error_code == '404':
            logger.warning('bucket {name} not found'.format(name=s3_bucket))
        else:
            logger.error('error querying for bucket {name} (code {code})'.format(
                name=s3_bucket,
                code=error_code))

    return s3, bucket


# move a file from castle to aws
def move_file(obj):
    _, bucket = get_bucket()
    if bucket is None:
        return

    # META DATA
    uid = IUUID(obj)
    if not uid:
        logger.info('Could not get uid of object')
        return
    key = KEY_PREFIX + uid
    filename = obj.file.filename
    if not isinstance(filename, unicode):
        filename = unicode(filename, 'utf-8', errors="ignore")
    filename = quote(filename.encode("utf8"))
    disposition = "attachment; filename*=UTF-8''%s" % filename
    size = obj.file.getSize()
    content_type = obj.file.contentType
    extraargs = {
        'ContentType': content_type,
        'ContentDisposition': disposition,
    }

    # Upload to AWS
    # valid modes in ZODB 3, 4 or 5 do not include 'rb' --
    #   see ZODB/blob.py line 54 (or so) for 'valid_modes'
    # note: upload_fileobj() does a multipart upload, which is why
    #   chunked uploading is no longer performed explicitly
    #   see: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Client.upload_fileobj  # noqa
    blob_fi = obj.file._blob.open('r')
    bucket.upload_fileobj(blob_fi, key, ExtraArgs=extraargs)

    # Delete data from ZODB, but leave a reference
    if not getCelery().conf.task_always_eager:
        obj._p_jar.sync()
    obj.file = NamedBlobFile(data='', contentType=obj.file.contentType, filename=FILENAME)
    obj.file.original_filename = filename
    obj.file.original_content_type = content_type
    obj.file.original_size = size

    set_permission(obj)


def set_permission(obj):
    s3, bucket = get_bucket()
    if bucket is None:
        return

    uid = IUUID(obj)
    key = KEY_PREFIX + uid

    # check if object is in aws
    s3_obj = bucket.Object(key)
    try:
        s3_obj.load()  # does HEAD request
    except botocore.exceptions.ClientError:
        logger.error(
            'error reading object {key} in bucket {name}'.format(
                key=key,
                name=bucket.name),
            log_exc=True)
        return

    # is the object public?
    perms = obj.rolesOfPermission("View")
    public = False
    for perm in perms:
        if perm["name"] == "Anonymous":
            if perm["selected"] != "":
                public = True
                break

    # set aws public/private and get url
    object_acl = s3_obj.Acl()
    if public:
        object_acl.put(ACL='public-read')
        # a public URL is not fetchable with no expiration, apparently
        expires_in = 0
        scheme, netloc, path, qs, anchor = urlsplit(s3.meta.client.meta.endpoint_url)
        # this makes sure there are no empty segments, and then appends
        # the bucket name and quoted key value (which is fine, and usable
        # with aws api)
        newpath = "/".join(filter(None, path.split("/")) + [bucket.name, quote_plus(key)])
        url = urlunsplit((scheme, netloc, newpath, qs, anchor))
    else:
        object_acl.put(ACL='private')
        expires_in = EXPIRES_IN
        params = {
            'Bucket': bucket.name,
            'Key': key,
        }
        url = s3_obj.meta.client.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=expires_in)

    annotations = IAnnotations(obj)
    info = annotations.get(STORAGE_KEY, PersistentMapping())
    info.update({
        'url': url,
        'expires_in': expires_in,
        'generated_on': time()
    })
    annotations[STORAGE_KEY] = info


# TODO: determine if the file obj in plone should also be deleted
# at this time, or document why it isn't, maybe. Content is all
# moved to aws anyway.
def delete_file(uid):
    _, bucket = get_bucket()
    if bucket is None:
        return

    key_name = KEY_PREFIX + uid
    try:
        key = bucket.Object(key_name)
        key.delete()
    except botocore.exceptions.ClientError:
        logger.error(
            'error deleting object {key} in bucket {name}'.format(
                key=key,
                name=bucket.name),
            log_exc=True)


def uploaded(obj):
    try:
        annotations = IAnnotations(obj)
    except TypeError:
        return False
    info = annotations.get(STORAGE_KEY, PersistentMapping())
    return 'url' in info


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
        basescheme, basenetloc, basepath, baseqs, baseanchor = urlsplit(base_url.decode('utf-8'))
        scheme, netloc, path, qs, anchor = urlsplit(url.decode('utf-8'))
        # make sure there are no empty segements
        # and also drop the first segment -- should be the bucket, which we
        # don't need to pass on to the final url
        newpath = u"/".join(filter(None, path.split(u'/'))[1:])
        url = urlunsplit((basescheme, basenetloc, newpath, qs, anchor))

    return url


def _one(val):
    """Wonky, values returning tuple sometimes?"""
    if type(val) in (tuple, list, set):
        if len(val) > 0:
            val = val[0]
        else:
            return
    return val


def get_url(obj):
    annotations = IAnnotations(obj)
    info = annotations.get(STORAGE_KEY, PersistentMapping())

    if info['expires_in'] != 0:
        # not public, check validity of url
        generated_on = info['generated_on']
        expires = datetime.fromtimestamp(generated_on + info['expires_in'])
        if datetime.utcnow() > expires:
            # need a new url
            s3, bucket = get_bucket()
            if bucket is not None:
                uid = IUUID(obj)
                key = KEY_PREFIX + uid
                params = {
                    'Bucket': bucket.name,
                    'Key': key,
                }
                url = s3.meta.client.generate_presigned_url(
                    'get_object',
                    Params=params,
                    ExpiresIn=EXPIRES_IN)

                info.update({
                    'url': url,
                    'generated_on': time(),
                    'expires_in': EXPIRES_IN
                })
                annotations[STORAGE_KEY] = info

    url = _one(info['url'])
    if not url.startswith('http'):
        url = 'https:' + url

    # need to make sure the url is formatted correctly
    # the main one we've seen is extra slashes in the path
    scheme, netloc, path, qs, anchor = urlsplit(url)
    # this will get rid of any empty segments
    path = "/".join(filter(None, path.split('/')))
    finalurl = urlunsplit((scheme, netloc, path, qs, anchor))
    return swap_url(finalurl)


def create_or_update(bucket, key, content_type, data, content_disposition=None, make_public=True):
    extraargs = {
        'ContentType': content_type,
    }
    if content_disposition is not None:
        extraargs['ContentDisposition'] = content_disposition
    contentio = StringIO.StringIO(data)
    bucket.upload_fileobj(contentio, key, ExtraArgs=extraargs)
    if make_public:
        s3_obj = bucket.Object(key)
        object_acl = s3_obj.Acl()
        object_acl.put(ACL='public-read')


def create_if_not_exists(bucket, key, content_type, data, content_disposition=None, make_public=True):
    try:
        # does a head request for a single key, will throw an error
        # if not found (or elsewise)
        bucket.Object(key).load()
    except botocore.exceptions.ClientError:
        # the object hasn't been pushed to s3 yet, so do that
        # create/update
        create_or_update(
            bucket,
            key,
            content_type,
            data,
            content_disposition=content_disposition,
            make_public=make_public)
