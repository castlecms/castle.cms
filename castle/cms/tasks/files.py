import logging

import transaction
from castle.cms.commands import md5
from castle.cms.files import aws
from castle.cms.media import video
from castle.cms.services.google import youtube
from castle.cms.utils import retriable
from collective.celery import task
from plone import api
from plone.app.blob.utils import openBlob
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility


logger = logging.getLogger(__name__)


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


@task()
def youtube_video_edited(obj):
    videofi = obj.file

    if videofi is not None and videofi.filename != aws.FILENAME:
        try:
            opened = openBlob(videofi._blob)
            bfilepath = opened.name
            opened.close()
        except IOError:
            logger.warn('error opening blob file')
            return

        # we can only edit if file has NOT changed
        # otherwise, it will be reuploaded and original deleted
        if md5 is not None:
            old_hash = getattr(obj, '_file_hash', None)
            if old_hash is not None:
                current_hash = md5(bfilepath)
                if old_hash != current_hash:
                    # dive out, we don't want to edit
                    return

    youtube.edit(obj)


@task()
def youtube_video_deleted(youtube_id):
    youtube.delete(youtube_id)


@task()
def youtube_video_state_changed(obj):
    if api.content.get_state(obj=obj, default='Unknown') == 'published':
        youtube.publish(obj)
    else:
        youtube.unlist(obj)
