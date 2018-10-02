# check failed login attempts
# lockout user if more than 5 for 15 minutes, send system message
from castle.cms import cache
from castle.cms.utils import get_ip
from datetime import datetime
from plone import api
from plone.memoize.instance import memoize
from plone.registry.interfaces import IRegistry
from time import time
from uuid import uuid4
from zope.component import getUtility

import cPickle
import logging


LOGGED_IN_MARKER_KEY = 'castle.cms.user-logged-in'

log = logging.getLogger(__name__)


class LockoutManager(object):

    def __init__(self, site, login):
        self.site = site
        self.login = login

        try:
            self.attempts = cache.get(self.cache_key)
        except (AttributeError, KeyError):
            self.attempts = []

        registry = getUtility(IRegistry)
        self.window = registry.get('plone.failed_login_attempt_window', 3600)
        self.max_number = registry.get('plone.max_failed_login_attempts', 15)

    @property
    @memoize
    def cache_key(self):
        return '%s-loginattempts-%s' % (
            '-'.join(self.site.getPhysicalPath()[1:]),
            self.login
        )

    def get_attempts_this_window(self):
        now = time()
        startperiod = now - self.window
        period_attempts = []
        for tt in self.attempts:
            if tt > startperiod and tt <= now:
                period_attempts.append(tt)
        return period_attempts

    def add_attempt(self):
        attempts = self.get_attempts_this_window()
        attempts.append(time())
        self.attempts = attempts
        self.save()

    def maxed_number_of_attempts(self):
        attempts = self.get_attempts_this_window()
        return len(attempts) >= self.max_number

    def clear(self):
        self.attempts = []
        self.save()

    def save(self):
        cache.set(self.cache_key, self.attempts)


class SessionManager(object):
    cookie_name = 'castle_session_id'

    def __init__(self, site, request, user):
        self.user = user
        self.site = site
        self.request = request
        self.session_id = self.request.cookies.get(self.cookie_name, None)

    def has_session_id(self):
        return self.session_id is not None

    @property
    @memoize
    def cache_key(self):
        return '%s-session-%s-%s' % (
            '-'.join(self.site.getPhysicalPath()[1:]),
            self.user.getId(),
            self.session_id
        )

    def register(self):
        self.session_id = uuid4()
        self.request.response.setCookie(self.cookie_name, self.session_id)
        self.log({})

    def get(self, cache_key=None):
        try:
            return cache.get(self.cache_key)
        except (AttributeError, KeyError):
            return None

    def log(self, session):
        session.update({
            'updated': datetime.utcnow().isoformat(),
            'ua': self.request.environ.get('HTTP_USER_AGENT', 'unknown'),
            'ip': get_ip(self.request),
            'userid': self.user.getId(),
            'id': self.session_id
        })
        # default of 5 hr sessions
        # ideally this matches cookie timeout
        cache.set(self.cache_key, session, expire=60 * 60 * 5)

    def expired(self, session):
        try:
            return session.get('expired', False)
        except Exception:
            return False

    def delete(self):
        try:
            cache.delete(self.cache_key)
        except Exception:
            pass

    def expire(self, session=None):
        if session is None:
            session = self.get()

        if session:
            session.update({
                'expired': True
            })
            cache.set(self.cache_key, session, expire=60 * 60 * 5)


def get_active_sessions(sessions_key=None):
    portal = api.portal.get()
    portal_path = '-'.join(portal.getPhysicalPath()[1:])
    if not sessions_key:
        sessions_key = '%s-session-*' % portal_path

    cclient = cache.get_client()
    sessions = []
    try:
        keys = cclient.client.keys(sessions_key)
        if keys:
            for session in cclient.client.mget(keys):
                try:
                    session = cPickle.loads(session)
                except Exception:
                    continue
                sessions.append(session)
            sessions = reversed(sorted(sessions, key=lambda x: x['updated']))
    except AttributeError:
        sessions = []

    # we'll also squash and cleanup duplicate sessions here...
    found = []
    filtered = []
    for session in sessions:
        compare_key = '%s%s%s' % (
            session.get('ua'),
            session.get('ip'),
            session.get('userid')
        )
        if compare_key in found:
            cache_key = '%s-session-%s-%s' % (
                portal_path,
                session['userid'],
                session['id']
            )
            try:
                cache.delete(cache_key)
            except Exception:
                pass
        else:
            try:
                session['user'] = api.user.get(session['userid'])
            except Exception:
                pass
            found.append(compare_key)
            filtered.append(session)
    return filtered
