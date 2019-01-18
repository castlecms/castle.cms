import json
import logging
import mimetypes
import time

from apiclient.http import MediaFileUpload
from castle.cms.interfaces import IUploadedToYoutube
from collective.celery.utils import getCelery
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.interface import alsoProvides

from . import get_service


logger = logging.getLogger('castle.cms')

DEFAULT_CHUNK_SIZE = -1  # one request, still resumable
MAX_RETRIES = 3
PRIVATE_VIDEO_STATUS = 'unlisted'

SCOPES = [
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/youtubepartner'
]


def get_oauth_token():
    registry = getUtility(IRegistry)
    oauth_token = registry.get('plone.google_oauth_token', None)
    if oauth_token is None:
        return
    try:
        return json.loads(oauth_token)
    except TypeError:
        return None


def get_youtube_service():
    oauth_token = get_oauth_token()
    return get_service('youtube', 'v3', SCOPES,
                       access_token=oauth_token['access_token'],
                       refresh_token=oauth_token['refresh_token'])


def should_upload(obj):
    if obj.portal_type != 'Video':
        return False

    if get_oauth_token() is None:
        return False
    value = getattr(obj, 'upload_to_youtube', None)
    if value is None or value in (False, 'false', 'False', 'f', '0'):
        return False
    return True


def upload(obj, filepath, privacy=PRIVATE_VIDEO_STATUS,
           chunksize=DEFAULT_CHUNK_SIZE, filename=None):
    # Should we use private instead of unlisted? I don't know here...

    try:
        service = get_youtube_service()
    except Exception:
        logger.error("Can't get youtube service.", exc_info=True)
        return False

    video_service = service.videos()

    body = dict(
        snippet=dict(
            title=obj.title,
            description=obj.description
        ),
        status=dict(
            privacyStatus=privacy
        )
    )

    mimetype = None
    if filename is not None:
        mimetype, _ = mimetypes.guess_type(filename)

    media_body = MediaFileUpload(
        filepath,
        mimetype=mimetype,
        chunksize=chunksize,
        resumable=True
    )

    insert_request = video_service.insert(
        body=body,
        part=",".join(body.keys()),
        media_body=media_body)

    resumable_upload(obj, service, insert_request)


def resumable_upload(obj, service, insert_request):
    response = None
    retry = 0
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            if 'id' in response:
                # uploaded successfully
                if not getCelery().conf.task_always_eager:
                    obj._p_jar.sync()
                obj.youtube_url = 'https://youtu.be/{id}'.format(
                    id=response['id'])
                if IUploadedToYoutube.providedBy(obj):
                    try:
                        delete(obj._youtube_video_id)
                    except Exception:
                        logger.warning(
                            'Error deleting existing youtube video: {}'.format(
                                obj._youtube_video_id
                            ), exc_info=True)
                obj._youtube_video_id = response['id']
                alsoProvides(obj, IUploadedToYoutube)
                _update_access_token(service)
            else:
                logger.error('Youtube upload failed with an unexpected'
                             ' response: {}'.format(response))
        except Exception:
            logger.warning(
                'An error occured while uploading to youtube {e}', exc_info=True)
            retry += 1
            time.sleep(3)
            if retry > MAX_RETRIES:
                # bubble up error
                raise


def _update_access_token(service):
    registry = getUtility(IRegistry)
    oauth_token = registry.get('plone.google_oauth_token', None)
    if oauth_token is None:
        return
    try:
        token = json.loads(oauth_token)
        creds = service._http.request.credentials
        current = creds.token_response
        if token['access_token'] != current['access_token']:
            current = current.copy()
            if 'refresh_token' not in current:
                current['refresh_token'] = creds.refresh_token
            registry['plone.google_oauth_token'] = json.dumps(
                current).decode('utf-8')
    except (TypeError, AttributeError, KeyError):
        pass


def _get_video(service, obj=None, video_id=None, part='snippet'):
    if obj is not None:
        video_id = obj._youtube_video_id
    video_service = service.videos()
    results = video_service.list(
        part=part,
        id=video_id
    ).execute()

    if len(results['items']) == 0:
        raise Exception('Expected video id {} to be found on youtube account'.format(
            video_id
        ))

    return results['items'][0]


def edit(obj):
    # update tile/description
    try:
        service = get_youtube_service()
    except Exception:
        logger.error("Can't get youtube service.", exc_info=True)
        return False
    video = _get_video(service, obj)
    video_service = service.videos()

    if (video['snippet']['title'] != obj.title or
            video['snippet']['description'] != obj.description):
        video['snippet']['title'] = obj.title
        video['snippet']['description'] = obj.description
        video_service.update(
            part='snippet',
            body=video
        ).execute()
    _update_access_token(service)


def publish(obj):
    try:
        service = get_youtube_service()
    except Exception:
        logger.error("Can't get youtube service.", exc_info=True)
        return False

    video = _get_video(service, obj, part='status')
    video_service = service.videos()
    video['status']['privacyStatus'] = 'public'
    video_service.update(
        part='status',
        body=video
    ).execute()
    _update_access_token(service)


def unlist(obj):
    try:
        service = get_youtube_service()
    except Exception:
        logger.error("Can't get youtube service.", exc_info=True)
        return False

    video = _get_video(service, obj, part='status')
    video_service = service.videos()
    video['status']['privacyStatus'] = PRIVATE_VIDEO_STATUS
    video_service.update(
        part='status',
        body=video
    ).execute()
    _update_access_token(service)


def delete(video_id):
    try:
        service = get_youtube_service()
    except Exception:
        logger.error("Can't get youtube service.", exc_info=True)
        return False
    video_service = service.videos()
    video_service.delete(
        id=video_id, onBehalfOfContentOwner=None).execute()
    _update_access_token(service)
