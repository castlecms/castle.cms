from Products.Five import BrowserView
from castle.cms.lockout import get_active_sessions
from plone.keyring.interfaces import IKeyManager
from plone.protect.authenticator import createToken, _is_equal, _getKeyring
from plone import api
from zope.component import getUtility
import json, hmac
try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


def chatInfo():

    frontpage = api.portal.get_registry_record('castle.rocket_chat_front_page')
    salt = api.portal.get_registry_record('castle.rocket_chat_secret')

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

        cookie = self.request.get('cookie')
        user = self.request.get('user')
        if cookie:
            self.request.set('_authenticator', cookie)

            salt = api.portal.get_registry_record('castle.rocket_chat_secret')

            manager = getUtility(IKeyManager)
            keyring = _getKeyring(user, manager=manager)
            for key in keyring:
                if key is None:
                    continue
                value = hmac.new(key, user + salt, sha).hexdigest()
                if _is_equal(value, cookie):
                    return json.dumps({
                        'status': 'success',
                        'user': user
                    })
        return json.dumps({ 'status': 'failure' })


class ChatView(BrowserView):

    def chatInfo(self):
        return json.dumps(chatInfo())
