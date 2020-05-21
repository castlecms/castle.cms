from AccessControl import Unauthorized
import botocore
from castle.cms import archival
from castle.cms.files import aws
from DateTime import DateTime
from plone import api
from plone.app.uuid.utils import uuidToObject
from Products.CMFPlone.resources import add_resource_on_request
from Products.Five import BrowserView
from zope.component import getMultiAdapter

import json
import logging


logger = logging.getLogger('castle.cms')


class BaseView(BrowserView):
    @property
    def enabled(self):
        return (api.portal.get_registry_record('castle.archival_enabled') and
                api.portal.get_registry_record('castle.aws_s3_bucket_name') and
                api.portal.get_registry_record('castle.aws_s3_key') and
                api.portal.get_registry_record('castle.aws_s3_secret') and
                api.portal.get_registry_record('plone.public_url'))


class Review(BaseView):
    def dump(self, item):
        return {
            'title': item.Title,
            'url': item.getURL(),
            'uid': item.UID,
            'modified': item.modified.pCommonZ()
        }

    def items(self):
        man = archival.ArchiveManager()
        return [self.dump(i) for i in man.getContentToArchive(30)]

    def json_dump(self):
        return json.dumps(self.items())

    def __call__(self):
        extend = self.request.form.get('extend')
        if extend:
            obj = uuidToObject(extend)
            obj.setModificationDate(DateTime())
            obj.reindexObject(idxs=['modified'])
            return self.json_dump()
        return self.index()


class AWSApi(object):
    def __init__(self, site, request):
        self.site = site
        self.request = request
        bucket_name = api.portal.get_registry_record('castle.aws_s3_bucket_name')
        self.s3, self.bucket = aws.get_bucket(bucket_name)
        self.archive_storage = archival.Storage(site)

    def __call__(self):
        method = self.request.form.get('method')
        if method == 'list':
            return self.list()
        elif method == 'get':
            return self.get()
        elif method == 'save':
            return self.save()
        elif method == 'delete':
            return self.delete()
        elif method == 'deletegroup':
            return self.deletegroup()

    def get(self):
        key_name = archival.CONTENT_KEY_PREFIX + self.request.form.get('path')
        key = self.bucket.get_object(Key=key_name)
        if 'html' not in key.content_type:
            raise Exception('Must be html...')
        return {
            'data': key.read()
        }

    def deletegroup(self):
        authenticator = getMultiAdapter((self.site, self.request), name=u"authenticator")
        # manually provide csrf here...
        if not authenticator.verify():
            raise Unauthorized

        paths = json.loads(self.request.form.get('paths'))

        # path can be folder or item... get all items and then do multi delete from aws api
        todelete = []
        for path in paths:
            if path.endswith('/'):
                # this is a folder, delete everything in it
                base_path = archival.CONTENT_KEY_PREFIX + path
                base_path = base_path.replace('//', '/').rstrip('/') + '/'
                for key in self.bucket.objects.filter(prefix=base_path):
                    self.delete_archive(key.name[len(archival.CONTENT_KEY_PREFIX):])
                    todelete.append(dict(Key=key.name))
            else:
                self.delete_archive(path)
                todelete.append(dict(Key=archival.CONTENT_KEY_PREFIX + path))

        # delete_objects maxes out at 1000 keys according to documentation
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Bucket.delete_objects
        if len(todelete) > 1000:
            i = 0
            while i < len(todelete):
                n = i + 1000
                self.bucket.delete_objects(
                    Delete=dict(Objects=todelete[i:n]))
                i += 1000
        else:
            self.bucket.delete_objects(Delete=dict(Objects=todelete))

    def delete(self):
        path = self.request.form.get('path')
        key_name = archival.CONTENT_KEY_PREFIX + path
        authenticator = getMultiAdapter((self.site, self.request), name=u"authenticator")
        # manually provide csrf here...
        if not authenticator.verify():
            raise Unauthorized

        try:
            key = self.bucket.get_object(Key=key_name)
            key.delete()
        except botocore.exceptions.ClientError:
            logger.error(
                'error deleting object {key} in bucket {name}'.format(
                    key=key_name,
                    name=self.bucket.name),
                log_exc=True)

        self.delete_archive(path)

    def delete_archive(self, path):
        path = '/' + path.strip('/')
        try:
            uid = self.archive_storage.path_to_uid[path]
        except KeyError:
            return
        try:
            del self.archive_storage.archives[uid]
        except Exception:
            pass

    def save(self):
        key_name = archival.CONTENT_KEY_PREFIX + self.request.form.get('path')
        authenticator = getMultiAdapter((self.site, self.request), name=u"authenticator")
        # manually provide csrf here...
        if not authenticator.verify():
            raise Unauthorized

        content = self.request.form.get('value')
        try:
            key = self.bucket.get_object(Key=key_name)
            key.put(
                ACL='public-read',
                Body=content,
                ContentType="text/html; charset=utf-8")
        except botocore.exceptions.ClientError:
            logger.error(
                'error saving object {key} in bucket {name}'.format(
                    key=key_name,
                    name=self.bucket.name),
                log_exc=True)

    def list(self):
        result = []
        base_path = archival.CONTENT_KEY_PREFIX + self.request.form.get('path', '')
        base_path = base_path.replace('//', '/').rstrip('/') + '/'
        for key in self.bucket.objects.filter(prefix=base_path):
            path = key.name[len(archival.CONTENT_KEY_PREFIX):]
            result.append({
                'path': path,
                'id': path.rstrip('/').split('/')[-1],
                'is_folder': False,
                'url': '{endpoint_url}/{bucket}/{key}'.format(
                    endpoint_url=self.s3.meta.endpoint_url,
                    bucket=self.bucket.name,
                    key=archival.CONTENT_KEY_PREFIX + path)
            })
        return result


class Manage(BaseView):

    def __call__(self):
        # utility function to add resource to rendered page
        add_resource_on_request(self.request, 'castle-components-manage-archives')
        return super(Manage, self).__call__()

        if self.request.form.get('api'):
            self.request.response.setHeader('Content-type', 'application/json')
            return json.dumps(AWSApi(self.context, self.request)())
        return self.index()
