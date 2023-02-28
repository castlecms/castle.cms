from collective.celery import task

from castle.cms.media import video
from castle.cms.utils import retriable


@retriable()
def _process_video(obj):
    video.process(obj)


@task()
def process_video(obj):
    _process_video(obj)
