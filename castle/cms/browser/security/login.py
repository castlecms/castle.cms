import json
import time

from castle.cms import _, authentication, cache, texting
from castle.cms.interfaces import (IAuthenticator, ISecureLoginAllowedView,
                                   ISiteSchema)
from castle.cms.utils import (get_managers, send_email, strings_differ,
                              is_backend)
from plone import api
from plone.protect.authenticator import createToken
from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from zope.component import getMultiAdapter, getUtility
from zope.component.interfaces import ComponentLookupError
from zope.i18n import translate
from zope.interface import implements


class SecureLoginView(BrowserView):
    implements(ISecureLoginAllowedView)

    def __init__(self, context, request):
        super(SecureLoginView, self).__init__(context, request)
        self.auth = self.authenticator = getMultiAdapter(
            (context, request), IAuthenticator)
        self.state_map = {
            self.auth.REQUESTING_AUTH_CODE: self.send_authorization,
            self.auth.CHECK_CREDENTIALS: self.login,
            self.auth.COUNTRY_BLOCKED: self.country_blocked
        }

    def __call__(self, reset=False):
        state = self.auth.get_secure_flow_state()
        if self.request.REQUEST_METHOD == 'POST':
            self.request.response.setHeader('Content-type', 'application/json')
            if not self.auth.two_factor_enabled and state == self.auth.REQUESTING_AUTH_CODE:
                state = self.auth.CHECK_CREDENTIALS
                self.auth.set_secure_flow_state(state)
            if state in self.state_map:
                return self.state_map[state]()
            elif not reset:
                self.auth.expire_secure_flow_state()
                self.auth.set_secure_flow_state(self.initial_state)
                return self.__call__(True)
            else:
                self.request.response.setStatus(403)
                return json.dumps({
                    'success': False,
                    'reason': 'Something went wrong.  Try again later.'
                })  # this shouldn't happen, state will expire.
        else:
            if state:
                self.auth.expire_secure_flow_state()
            self.auth.set_secure_flow_state(self.initial_state)

            if self.request.cookies.get('castle_session_id', None) in ['test_session', 'test_session_2']:
                return 'test-view'

            self.request.response.setHeader('X-Theme-Applied', True)
            return self.index()

    @property
    def initial_state(self):
        if self.auth.two_factor_enabled:
            return self.auth.REQUESTING_AUTH_CODE
        else:
            return self.auth.CHECK_CREDENTIALS

    @property
    def username(self):
        return self.request.form.get('username', None)

    @property
    def from_backend_url(self):
        return is_backend(self.request)

    def scrub_backend(self):
        if not self.auth.is_zope_root and self.from_backend_url:
            return api.portal.get_registry_record('plone.scrub_title_logo_to_backend_login')
        return False

    def get_country_header(self):
        return (
            self.request.get_header('Cf-Ipcountry') or
            self.request.get_header('Country'))

    def country_blocked(self):
        if self.request.form.get('apiMethod', None) == 'request_country_exception':
            user = api.user.get(username=self.username)
            cache_key = self.auth.get_country_exception_cache_key(user.getId)
            try:
                request_data = cache.get(cache_key)
            except KeyError:
                request_data = None

            if not request_data:
                self.request_country_exception()
            else:
                if request_data.get('granted', False):
                    self.auth.set_secure_flow_state(self.auth.CHECK_CREDENTIALS)
                    return json.dumps({
                        'success': True,
                        'messsage': 'Your request has already been granted, try logging in again.'
                                    ' Requests expire 12 hours after issue.'
                    })
                else:
                    return json.dumps({
                        'success': True,
                        'message': 'Your request has been issued, but not yet granted.'
                                   ' Requests expire 12 hours after issue.'
                    })

    def request_country_exception(self):
        req_country = self.get_country_header()
        user = api.user.get(username=self.username)
        data = self.auth.issue_country_exception_request(user, req_country)

        email_subject = "Country block exception request(Site: %s)" % (
            api.portal.get_registry_record('plone.site_title'))

        for admin_user in get_managers():
            if admin_user.getId() == user.getId():
                # it could be an admin, do not allow him to authorize himself
                continue

            admin_email = admin_user.getProperty('email')

            email_data = data.copy()
            email_data.update({
                'admin_name': (admin_user.getProperty('fullname') or
                               admin_user.getUserName()),
                'name': (user.getProperty('fullname') or user.getUserName()),
                'auth_link': '{}/authorize-country-login?code={}&userid={}'.format(
                    self.context.absolute_url(),
                    data['code'],
                    user.getId()
                )
            })
            email_html = '''
<p>
Hello {admin_name},
</p>
<p>
There has been a request to suspend country login restrictions for this site.

<p>
The user requesting this access logged this information:
</p>
<ul>
<li><b>Username</b>: {username}</li>
<li><b>Name</b>: {name}</li>
<li><b>Country</b>: {country}</li>
<li><b>IP</b>: {ip}</li>
</ul>

<p>The user has 12 hours between after authorization has been giving to login
   with the temporary access</p>

<p>If you'd like to authorize this user, please click this link:
   <a href="{auth_link}">authorize {username}</a>
</p>'''.format(**email_data)
            send_email(admin_email, email_subject, html=email_html)

        return json.dumps({
            'success': True,
            'message': 'Successfully requested country exception.',
            'messageType': 'info'
        })

    def login(self):
        logged_in = False

        if not self.username:
            self.request.response.setHeader('X-Theme-Applied', True)
            self.request.response.setHeader('Content-type', 'text/html')
            return self.index()

        if self.auth.two_factor_enabled:
            if self.request.form.get('apiMethod', None) == 'resendAuth':
                self.auth.set_secure_flow_state(self.auth.REQUESTING_AUTH_CODE)
                return json.dumps({
                    'success': True,
                    'message': 'You may request another auth code.'
                })
            code = self.request.form.get('code')
            if not self.auth.authorize_2factor(self.username, code):
                return json.dumps({
                    'success': False,
                    'message': 'Two Factor is enabled, code not authorized.'
                })

        if getattr(self.context, 'portal_registry', None):
            backend_urls = self.context.portal_registry['plone.backend_url']
            only_allow_login_to_backend_urls = self.context.portal_registry['plone.only_allow_login_to_backend_urls']  # noqa
            portal_url = api.portal.get().absolute_url()
            bad_domain = only_allow_login_to_backend_urls and \
                         len(backend_urls) > 0 and \
                         portal_url.rstrip('/') not in backend_urls and \
                         portal_url.rstrip('/') + '/' not in backend_urls
            if bad_domain:
                return json.dumps({
                    'success': False,
                    'message': translate(_(
                        u'description_bad_login_domain',
                        default=u'You are attempting to log into this site from the wrong domain; contact your site administrator for assistance.'  # noqa
                    ))
                })

        try:
            logged_in, user = self.auth.authenticate(
                username=self.username,
                password=self.request.form.get('password'),
                country=self.get_country_header(),
                login=True
            )
        except authentication.AuthenticationMaxedLoginAttempts:
            return json.dumps({
                'success': False,
                'message': 'You have reached the max number of login attempts '
                           'for a period.'
            })
        except authentication.AuthenticationUserDisabled:
            return json.dumps({
                'success': False,
                'message': 'User is disabled.'
            })
        except authentication.AuthenticationCountryBlocked:
            self.auth.set_secure_flow_state(self.auth.COUNTRY_BLOCKED)
            return json.dumps({
                'success': False,
                'countryBlocked': True,
                'message': 'User login blocked. The country you are logging '
                           'in from is blocked.'
            })
        except authentication.AuthenticationPasswordResetWindowExpired:
            return json.dumps({
                'success': False,
                'message': 'User login disabled. Password reset request not '
                           'fullfilled in required time period.'
            })

        if not self.auth.is_zope_root and user:
            pw_expired = user.getProperty(
                'reset_password_required', False)
            if pw_expired:
                resp = {
                    'success': True,
                    'message': 'Your password has expired. Change it within 24 hours, or this account will be locked.',  # noqa
                    'changePasswordRequired': True,
                    'changePasswordUrl': api.portal.get().absolute_url() + '/@@change-password',
                }
                return json.dumps(resp)

        if logged_in:
            self.auth.expire_secure_flow_state()
            resp = {
                'success': True,
            }
            try:
                with api.env.adopt_user(user=user):
                    resp['authenticator'] = createToken()
                    return json.dumps(resp)
            except Exception:
                resp['authenticator'] = createToken()
                return json.dumps(resp)

        return json.dumps({
            'success': False,
            'message': 'Login failed.'
        })

    def authorize_code(self):
        code = self.request.form.get('code')
        if self.authenticator.authorize_2factor(self.username, code):
            new_state = self.auth.CHECK_CREDENTIALS
            self.auth.set_secure_flow_state(new_state)
            return json.dumps({
                'success': True,
                'message': 'Authorization code verified.',
                'state': new_state
            })
        else:
            return json.dumps({
                'success': False,
                'message': 'Failed to authorize code'
            })

    def send_authorization(self):
        auth_type = self.request.form.get('authType') or 'email'
        if auth_type == 'email':
            self.send_auth_email()
        elif auth_type == 'sms':
            self.send_auth_text()

        # send_* return false when a root acl_user tries to log in to a site
        # with 2factor enabled.  They need to log in at the root.
        # For now, responding the same regardless for security reasons.

        new_state = self.auth.CHECK_CREDENTIALS
        self.auth.set_secure_flow_state(new_state)
        return json.dumps({
            'success': True,
            'message': 'Authorization code sent to provided username.',
            'state': new_state
        })

    def send_auth_email(self):
        email = None
        user = api.user.get(username=self.username)
        if user:
            email = user.getProperty('email')
        if not email:
            return

        code = self.auth.issue_2factor_code(self.username)
        registry = getUtility(IRegistry)
        site_settings = registry.forInterface(ISiteSchema,
                                              prefix="plone",
                                              check=False)
        html = """
<p>
    You have requested to authorize access to {title}.
</p>
<p>
    You authorization code is: {code}
</p>""".format(title=site_settings.site_title,
               code=code)

        send_email(
            [email], "Authorization code(%s)" % site_settings.site_title,
            html=html)

        return True

    def send_auth_text(self):
        phone = None
        user = api.user.get(username=self.username)
        if user:
            phone = user.getProperty('phone_number')

        if not phone:
            return

        registry = getUtility(IRegistry)
        site_settings = registry.forInterface(ISiteSchema,
                                              prefix="plone",
                                              check=False)

        code = self.auth.issue_2factor_code(self.username)

        text_message = '{}: phone verification code: {}'.format(
            site_settings.site_title, code)

        return texting.send(text_message, phone)

    def get_registry(self):
        try:
            return getUtility(IRegistry)
        except ComponentLookupError:
            pass

    def get_tool(self, name):
        if self.auth.is_zope_root:
            return getattr(self.context, name, None)
        else:
            return api.portal.get_tool(name)

    def options(self):
        return json.dumps(self.auth.get_options())


class LoginExceptionApprovalView(BrowserView):
    implements(ISecureLoginAllowedView)

    message = 'Incorrect code for country exception.'
    success = False

    def __call__(self):
        auth = self.authenticator = getMultiAdapter(
            (self.context, self.request), IAuthenticator)

        userid = self.request.form.get('userid')
        code = self.request.form.get('code')
        if userid and code:
            exc_key = auth.get_country_exception_cache_key(userid)
            try:
                data = cache.get(exc_key)
                if not strings_differ(data['code'], code):
                    timestamp = data.get('timestamp')
                    if timestamp and (time.time() < (timestamp + (12 * 60 * 60))):
                        user = api.user.get(data['userid'])
                        self.message = 'Successfully issued country login exception for {}({}).'.format(  # noqa
                            user.getProperty('fullname') or user.getUserName(),
                            user.getUserName())
                        self.success = True
                        data['granted'] = True
                        data['timestamp'] = time.time()
                        cache.set(exc_key, data, 12 * 60 * 60)
                        self.send_email(data)
            except Exception:
                pass
        return self.index()

    def send_email(self, user, data):
        email_subject = "Country block exception request granted(Site: %s)" % (
            api.portal.get_registry_record('plone.site_title'))

        email = user.getProperty('email')

        email_data = data.copy()
        email_data.update({
            'name': (user.getProperty('fullname') or user.getUserName())
        })
        email_html = '''
<p>
Hello {name},
</p>
<p>
Your request to login from your current location is granted.
<br />
Please login again with the same browser and location you made the request.
If you still experience any problems, please contact your administrator.

<p>
User and location information:
</p>
<ul>
<li><b>Username</b>: {username}</li>
<li><b>Name</b>: {name}</li>
<li><b>Country</b>: {country}</li>
<li><b>IP</b>: {ip}</li>
</ul>

<p>You have 12 hours to use this granted login exception.</p>
'''.format(**email_data)
        send_email(email, email_subject, html=email_html)
