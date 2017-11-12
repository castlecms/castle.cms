from castle.cms import ua
from castle.cms.lockout import get_active_sessions
from castle.cms.lockout import SessionManager
from plone import api
from Products.Five import BrowserView


class SessionsView(BrowserView):
    label = 'Active Sessions'
    description = "View and control your site's currently logged-in user sessions."

    def __call__(self):

        if self.request.REQUEST_METHOD == 'POST' and self.request.form.get('id'):
            session_id = self.request.form.get('id')
            user_id = self.request.form.get('userid')
            user = api.user.get(user_id)
            sm = SessionManager(self.context, self.request, user)
            sm.session_id = session_id
            sm.expire()

        self.sessions = get_active_sessions()

        return super(SessionsView, self).__call__()

    def parse_ua(self, session):
        return '%s: %s' % ua.simple_detect(session['ua'])
