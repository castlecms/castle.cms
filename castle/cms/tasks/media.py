from castle.cms.media import video
from castle.cms.utils import retriable
from collective.celery import task


@retriable()
def _process_video(obj):
    video.process(obj)


@task()
def process_video(obj):
    _process_video(obj)
