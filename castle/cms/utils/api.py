from datetime import timedelta, datetime
from Products.statusmessages.interfaces import IStatusMessage
from plone.registry.interfaces import IRegistry
from requests import post
from zope.component import getUtility
from zope.globalrequest import getRequest

import plone.api as api


def verify_recaptcha(req=None):
    if req is None:
        req = getRequest()

    registry = getUtility(IRegistry)
    key = registry.get('castle.recaptcha_private_key', '')
    if not key:
        # do not bother verifying if no key is defined
        return True
    code = req.form.get('g-recaptcha-response', '')
    remote_addr = req.get(
        'HTTP_X_FORWARDED_FOR',
        ''
    ).split(',')[0]
    if not remote_addr:
        remote_addr = req.get('REMOTE_ADDR')

    resp = post(
        'https://www.google.com/recaptcha/api/siteverify',
        data=dict(
            secret=key,
            response=code,
            remoteip=remote_addr
        ),
    )
    try:
        return resp.json()['success']
    except Exception:
        return False


def get_current_status_messages(request=None):
    request = request or getRequest()
    if not request:
        return []
    messages = []
    for message in IStatusMessage(request).get_all():
        if 'text' in message and 'timestamp' in message:
            try:
                messages.append({
                    'text': message['text'],
                    'datetime': datetime.fromtimestamp(message['timestamp']),
                })
            except Exception:
                continue
    return messages


def add_portal_message(message, message_type, request=None, allow_duplicates=False ):
    SAME_REQUEST_SECONDS_LIMIT = 10
    request = request or getRequest()
    if not request:
        return
    # sometimes, messages stick around for a while, so this timedelta hack allows us to ignore multiple
    # messages that are within a certain time interval of this attempt to add a portal message.
    # 10 seconds seems reasonable, but we can adjust as needed
    duplicate_exists = False
    if allow_duplicates is False:
        now = datetime.now()
        for message_data in get_current_status_messages(request):
            has_duplicate = (
                message_data['text'] == message and
                message_data['datetime'] + timedelta(seconds=SAME_REQUEST_SECONDS_LIMIT) >= now
            )
            if has_duplicate:
                duplicate_exists = True
                break
    # if True:
    if duplicate_exists is False:
        api.portal.show_message(
            message,
            request=request,
            type=message_type,
        )
