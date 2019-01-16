import requests
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.globalrequest import getRequest


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

    resp = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data=dict(
            secret=key,
            response=code,
            remoteip=remote_addr
        )
    )
    try:
        return resp.json()['success']
    except Exception:
        return False
