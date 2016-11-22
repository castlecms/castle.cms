from castle.cms.files import aws
from castle.cms.media import video
from castle.cms.utils import retriable
from collective.celery import task
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility

import transaction


def _clean_aws(obj):
    annotations = IAnnotations(obj)
    if aws.STORAGE_KEY in annotations and obj.file.filename != aws.FILENAME:
        del annotations[aws.STORAGE_KEY]
        aws.delete_file(IUUID(obj))


@task()
def file_edited(obj):
    _file_edited(obj)


@retriable()
def _file_edited(obj):
    try:
        if not obj.file:
            return _clean_aws(obj)
    except AttributeError:
        return
    if obj.portal_type == 'Video':
        video.process(obj)
        transaction.commit()

    if obj.portal_type not in ('Video', 'Audio', 'File'):
        return _clean_aws(obj)

    if 'pdf' in obj.file.contentType:
        # we also aren't moving pdfs out of here
        return _clean_aws(obj)

    registry = getUtility(IRegistry)
    if registry.get('castle.aws_s3_key', None) is None:
        return

    max_size_mb = registry.get('castle.max_file_size', 50)
    max_size = max_size_mb * 1024 * 1024
    if obj.file.getSize() > max_size:
        aws.move_file(obj)
    else:
        return _clean_aws(obj)


@task()
def workflow_updated(obj):
    annotations = IAnnotations(obj)
    if aws.STORAGE_KEY in annotations:
        aws.set_permission(obj)


@task()
def aws_file_deleted(uid):
    aws.delete_file(uid)
