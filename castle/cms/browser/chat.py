from plone import api
from plone.keyring.interfaces import IKeyManager
from plone.protect.authenticator import _getKeyring
from plone.protect.authenticator import _is_equal
from plone.protect.authenticator import createToken
from Products.Five import BrowserView
from zope.component import getUtility
from plone.api.exc import InvalidParameterError

import hmac
import json


try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


def get_chat_info():

    try:
        frontpage = api.portal.get_registry_record('castle.rocket_chat_front_page')
        salt = api.portal.get_registry_record('castle.rocket_chat_secret')
    except InvalidParameterError:
        frontpage = None
        salt = ''

    if frontpage is None or salt == '':
        return

    if frontpage[-1] != '/':
        frontpage = frontpage + '/'

    url = frontpage.replace('http://', 'ws://')
    url = url + 'websocket'

    current = api.user.get_current()
    base_url = api.portal.get().absolute_url()

    return {
        'url': url,
        'base_url': base_url,
        'frontpage': frontpage,
        'token': createToken(salt),
        'user': getattr(current, 'id', ''),
        'email': current.getProperty('email')
    }


class ChatLogin(BrowserView):

    def __call__(self):

        self.request.response.setHeader('Content-Type', 'application/json')

        token = self.request.get('token')
        user = self.request.get('user')

        if token:
            salt = api.portal.get_registry_record('castle.rocket_chat_secret')

            manager = getUtility(IKeyManager)
            keyring = _getKeyring(user, manager=manager)
            for key in keyring:
                if key is None:
                    continue
                value = hmac.new(key, user + salt, sha).hexdigest()
                if _is_equal(value, token):
                    return json.dumps({
                        'status': 'success',
                        'user': user
                    })
        return json.dumps({'status': 'failure'})


class ChatView(BrowserView):

    def chatInfo(self):
        return json.dumps(get_chat_info())
