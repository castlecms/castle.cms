import time

from Acquisition import aq_parent
from castle.cms import cache
from castle.cms.interfaces import IAuthenticator
from castle.cms.interfaces import ICastleApplication
from castle.cms.lockout import LockoutManager
from castle.cms.utils import get_ip
from castle.cms.utils import get_random_string
from castle.cms.utils import strings_differ
from OFS.interfaces import IItem
from plone import api
from plone.keyring.interfaces import IKeyManager
from plone.keyring.keymanager import KeyManager
from plone.protect.authenticator import createToken
from plone.registry.interfaces import IRegistry
from plone.session.plugins.session import manage_addSessionPlugin
from Products.CMFCore.interfaces import ISiteRoot
from Products.PlonePAS.events import UserLoggedInEvent
from Products.PlonePAS.setuphandlers import activatePluginInterfaces
from Products.PlonePAS.setuphandlers import migrate_root_uf
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from ZODB.POSException import ConnectionStateError
from zope.component import adapter
from zope.component import getGlobalSiteManager
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from zope.event import notify
from zope.interface import Interface
from zope.interface import implementer
from uuid import uuid4


class AuthenticationException(Exception):
    pass


class AuthenticationCountryBlocked(AuthenticationException):
    pass


class AuthenticationMaxedLoginAttempts(AuthenticationException):
    pass


class AuthenticationUserDisabled(AuthenticationException):
    pass


class AuthenticationPasswordResetWindowExpired(AuthenticationException):
    pass


@implementer(IAuthenticator)
@adapter(IItem, Interface)
class Authenticator(object):

    REQUESTING_AUTH_CODE = 'requesting-auth-code'
    CHECK_CREDENTIALS = 'check-credentials'
    COUNTRY_BLOCKED = 'country-blocked'

    def __init__(self, context, request):
        self.context = context
        self.request = request

        self.login_session_id = self.request.cookies.get('__sl__', None)
        if not self.login_session_id:
            self.set_login_session_id()

        self.valid_flow_states = [
            self.REQUESTING_AUTH_CODE,
            self.CHECK_CREDENTIALS,
            self.COUNTRY_BLOCKED,
        ]

        try:
            self.registry = getUtility(IRegistry)
        except ComponentLookupError:
            self.registry = None

    @property
    def is_zope_root(self):
        return ICastleApplication.providedBy(self.context)

    @property
    def two_factor_enabled(self):
        enabled = False
        if not self.is_zope_root and self.registry:
            enabled = self.registry.get('plone.two_factor_enabled', False)
        return enabled

    @property
    def expire(self):
        expire = 120
        if not self.is_zope_root and self.registry:
            expire = self.registry.get('plone.auth_step_timeout', 120)
        return expire

    def get_tool(self, name):
        if self.is_zope_root:
            return getattr(self.context, name, None)
        else:
            return api.portal.get_tool(name)

    def get_supported_auth_schemes(self):
        auth_schemes = [{
            'id': 'email',
            'label': 'Email'
        }]
        if self.registry:
            if self.registry.get('castle.plivo_auth_id'):
                auth_schemes.append({
                    'id': 'sms',
                    'label': 'SMS'
                })
        return auth_schemes

    def set_login_session_id(self):
        self.login_session_id = uuid4()
        self.request.response.setCookie('__sl__', self.login_session_id)

    def get_secure_flow_key(self):
        return '{id}-secure-state'.format(id=self.login_session_id)

    def set_secure_flow_state(self, state=None):
        if state not in self.valid_flow_states:
            return False

        cache_key = self.get_secure_flow_key()
        new_state = {
            'state': state,
            'timestamp': time.time()
        }
        cache.set(cache_key, new_state, expire=self.expire)
        return True

    def get_secure_flow_state(self):
        key = self.get_secure_flow_key()
        try:
            state_with_timestamp = cache.get(key)
            state = state_with_timestamp['state']
        except KeyError:
            state = None

        return state

    def expire_secure_flow_state(self):
        key = self.get_secure_flow_key()
        try:
            cache.delete(key)
        except Exception:
            pass
        self.set_login_session_id()

    def authorize_2factor(self, username, code, offset=0):
        if not code:
            return False

        try:
            value = cache.get(self.get_2factor_code_key(username))
        except Exception:
            return False

        # check actual code
        if strings_differ(value['code'].lower(), code.lower()):
            return False

        # then check timing
        timestamp = value.get('timestamp')
        if not timestamp or (time.time() > (timestamp + 5 * 60 + offset)):
            return False
        return True

    def get_2factor_code_key(self, username):
        return '{}-{}-auth-code-attempt'.format(
            '-'.join(self.context.getPhysicalPath()[1:]),
            username
        )

    def issue_2factor_code(self, username):
        cache_key = self.get_2factor_code_key(username)
        code = get_random_string(8).upper()
        # store code to check again later
        cache.set(cache_key, {
            'code': code,
            'timestamp': time.time()
        })
        return code

    def authenticate(self, username=None, password=None,
                     country=None, login=True):
        """return true if successful
        login: if a successful authentication should result in the user being
               logged in
        """
        if not self.is_zope_root:
            manager = LockoutManager(self.context, username)

            if manager.maxed_number_of_attempts():
                raise AuthenticationMaxedLoginAttempts()

            manager.add_attempt()

        for acl_users in self.get_acl_users():
            # if not root, could be more than one to check against
            user = acl_users.authenticate(username, password, self.request)
            if user:
                break

        if user is None:
            return False, user

        if not self.is_zope_root:
            manager.clear()

        if user.getRoles() == ['Authenticated']:
            raise AuthenticationUserDisabled()

        if self.registry:
            allowed_countries = self.registry.get(
                'plone.restrict_logins_to_countries')
            if allowed_countries and country:
                if country not in allowed_countries:
                    if not self.country_exception_granted(user.getId()):
                        raise AuthenticationCountryBlocked()

        if not self.is_zope_root:
            member = api.user.get(user.getId())
            reset_password = member.getProperty(
                'reset_password_required', False)
            reset_time = member.getProperty('reset_password_time', None)

            if reset_password and reset_time:
                if reset_time + (24 * 60 * 60) < time.time():
                    raise AuthenticationPasswordResetWindowExpired()

        if login:
            acl_users.session._setupSession(
                user.getId(), self.request.response)
            try:
                notify(UserLoggedInEvent(user))
            except ConnectionStateError:
                # On root login, it's possible no db state
                # is loaded but the key ring needs to be rotated.
                # This can cause an difficult to reproduce error.
                # Really, we don't care so much if we see this
                # error here. It'll get rotated another time.
                pass

        return True, user

    def country_exception_granted(self, userid):
        cache_key = self.get_country_exception_cache_key(userid)
        try:
            data = cache.get(cache_key)
        except Exception:
            return False
        timestamp = data.get('timestamp')
        if (data.get('granted') and timestamp and
                (time.time() < (timestamp + (12 * 60 * 60)))):
            return True
        return True

    def get_acl_users(self):
        """
        get list of acl_user objects,
        first, site, then root
        """
        objects = [self.get_tool('acl_users')]
        if not self.is_zope_root:
            context = aq_parent(self.context)
            while context and not ICastleApplication.providedBy(context):
                context = aq_parent(context)
            acl = getattr(context, 'acl_users', None)
            if acl:
                objects.append(acl)
        return objects

    def get_country_exception_cache_key(self, userid):
        return '{}-{}-country-exception'.format(
            '-'.join(self.context.getPhysicalPath()[1:]),
            userid
        )

    def issue_country_exception_request(self, user, country):
        # capture information about the request
        data = {
            'referrer': self.request.get_header('REFERER'),
            'user_agent': self.request.get_header('USER_AGENT'),
            'ip': get_ip(self.request),
            'username': user.getUserName(),
            'userid': user.getId(),
            'country': country,
            'timestamp': time.time(),
            'code': get_random_string(50),
            'granted': False
        }

        cache_key = self.get_country_exception_cache_key(user.getId())
        cache.set(cache_key, data, 12 * 60 * 60)  # valid for 12 hours

        return data

    def get_options(self):
        site_url = success_url = self.context.absolute_url()
        if ISiteRoot.providedBy(self.context):
            success_url += '/@@dashboard'
        if 'came_from' in self.request.form:
            came_from = self.request.form['came_from']
            try:
                url_tool = api.portal.get_tool('portal_url')
            except api.exc.CannotGetPortalError:
                url_tool = None
            if (came_from.startswith(site_url) and (
                    not url_tool or url_tool.isURLInPortal(came_from))):
                success_url = came_from
            if 'login' in success_url or 'logged_out' in success_url:
                if ISiteRoot.providedBy(self.context):
                    success_url = site_url + '/@@dashboard'
                else:
                    success_url = site_url  # zope root
            elif 'manage' in success_url:
                if ISiteRoot.providedBy(self.context):
                    success_url = site_url + '/@@dashboard'
                # else zope root, allow /manage here

        data = {
            'supportedAuthSchemes': self.get_supported_auth_schemes(),
            'twoFactorEnabled': self.two_factor_enabled,
            'apiEndpoint': '{}/@@secure-login'.format(site_url),
            'successUrl': success_url,
            'additionalProviders': [],
            'state': self.get_secure_flow_state()
        }
        try:
            data['authenticator'] = createToken()
        except ConnectionStateError:
            # zope root related issue here...
            pass

        return data


def install_acl_users(app, event):
    logger = event.commit
    uf = app.acl_users
    found = uf.objectIds(['Plone Session Plugin'])
    if not found:
        # new root acl user implementation not installed yet
        migrate_root_uf(app)
        uf = app.acl_users  # need to get new acl_users

        plone_pas = uf.manage_addProduct['PlonePAS']
        manage_addSessionPlugin(plone_pas, 'session')
        activatePluginInterfaces(app, "session")

        cookie_auth = uf.credentials_cookie_auth
        cookie_auth.login_path = u'/@@secure-login'

        uf.plugins.activatePlugin(
            IChallengePlugin,
            'credentials_cookie_auth'
        )

        # also delete basic auth
        uf.manage_delObjects(['credentials_basic_auth'])

        # for some reason, we need to install the initial user...
        if not api.env.test_mode():
            try:
                uf.users.manage_addUser('admin', 'admin', 'admin', 'admin')
                uf.roles.assignRoleToPrincipal('Manager', 'admin')
            except KeyError:
                pass  # already a user

        if logger is not None:
            logger('Updated acl users')

    km = getattr(app, 'key_manager', None)
    if km is None:
        km = KeyManager()
        app.key_manager = km
        app._p_changed = 1
        if logger is not None:
            logger('adding key manager')

    sm = getGlobalSiteManager()
    sm.registerUtility(km, IKeyManager)
