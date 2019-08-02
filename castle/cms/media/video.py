import os
from logging import getLogger
from shutil import copyfile, rmtree
from tempfile import mkdtemp

from castle.cms.commands import avconv, md5
from castle.cms.files import aws
from castle.cms.services.google import youtube
from collective.celery.utils import getCelery
from plone.app.blob.utils import openBlob
from plone.namedfile import NamedBlobImage
from plone.namedfile.file import NamedBlobFile


logger = getLogger(__name__)


def switchFileExt(filename, ext):
    filebase = filename.rsplit('.', 1)[0]
    return filebase + '.' + ext


def process(context):
    video = context.file
    if not video or video.filename == aws.FILENAME:
        return

    try:
        opened = openBlob(video._blob)
        bfilepath = opened.name
        opened.close()
    except IOError:
        logger.warn('error opening blob file')
        return

    # by default, assume all non-mp4 videos need to be converted
    # but in reality, all videos need converting, even mp4.
    # md5 is only what makes this possible
    convert_it = video.contentType.split('/')[-1] != 'mp4'
    if md5 is not None:
        old_hash = getattr(context, '_file_hash', None)
        current_hash = md5(bfilepath)
        if old_hash is None or old_hash != current_hash:
            convert_it = True

    if context.image and not convert_it:
        # already an mp4 and already has a screen grab
        return

    if convert_it and youtube.should_upload(context):
        try:
            youtube.upload(context, bfilepath, filename=video.filename)
            # saving hash tells us we do not need to convert anymore...
            context._file_hash = md5(bfilepath)
            convert_it = False
        except Exception:
            logger.error('Error uploading youtube video', exc_info=True)

    tmpdir = mkdtemp()
    tmpfilepath = os.path.join(tmpdir, video.filename)
    copyfile(bfilepath, tmpfilepath)

    if convert_it:
        output_filepath = os.path.join(tmpdir, 'output.mp4')
        try:
            avconv.convert(tmpfilepath, output_filepath)
        except Exception:
            logger.info('Could not convert video', exc_info=True)
        if (os.path.exists(output_filepath) and
                os.path.getsize(output_filepath) > 0):
            if md5 is not None:
                try:
                    context._file_hash = md5(output_filepath)
                except Exception:
                    logger.info('Could not get md5', exc_info=True)
            if not getCelery().conf.task_always_eager:
                context._p_jar.sync()
            fi = open(output_filepath)
            namedblob = NamedBlobFile(
                fi, filename=switchFileExt(video.filename, 'mp4'))
            context.file = namedblob
            fi.close()

    if not context.image:
        # try and grab one from video
        output_filepath = os.path.join(tmpdir, u'screengrab.png')
        try:
            avconv.grab_frame(tmpfilepath, output_filepath)
            if os.path.exists(output_filepath):
                fi = open(output_filepath)
                context.image = NamedBlobImage(fi, filename=u'screengrab.png')
                fi.close()
        except Exception:
            logger.warning(
                'error getting thumbnail from video', exc_info=True)
    rmtree(tmpdir)
