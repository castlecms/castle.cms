import hmac
import json

from castle.cms.utils import get_chat_info
from plone import api
from plone.keyring.interfaces import IKeyManager
from plone.protect.authenticator import _getKeyring
from plone.protect.authenticator import _is_equal
from Products.Five import BrowserView
from zope.component import getUtility


try:
    from hashlib import sha1 as sha
except ImportError:
    import sha


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
