from Products.Five import BrowserView
from castle.cms.lockout import get_active_sessions
from plone import api
import json


def chatInfo():

    url = api.portal.get_registry_record('castle.rocket_chat_server')
    frontpage = api.portal.get_registry_record('castle.rocket_chat_front_page')

    current = api.user.get_current()

    portal = api.portal.get()
    portal_path = '-'.join(portal.getPhysicalPath()[1:])

    user_token_stub = '%s-session-%s-' % (portal_path, current.id)

    base_url = api.portal.get().absolute_url()
    return {
        'url': url,
        'base_url': base_url,
        'frontpage': frontpage,
        'token': user_token_stub,
        'user': getattr(current, 'id', ''),
        'email': current.getProperty('email')
    }

class ChatLogin(BrowserView):

    def __call__(self):

        self.request.response.setHeader('Content-Type', 'application/json')

        cookie = self.request.get('cookie')
        if cookie:
            session = get_active_sessions(cookie)
            if session:

                user = session[0]['user']
                return json.dumps({
                    'status': 'success',
                    'user': user.getUserName()
                })

        return json.dumps({ 'status': 'failure' })


class ChatView(BrowserView):

    def chatInfo(self):
        return json.dumps(chatInfo())
