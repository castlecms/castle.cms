import json
import time

from castle.cms import _, authentication, cache, texting
from castle.cms.interfaces import (IAuthenticator, ISecureLoginAllowedView,
                                   ISiteSchema)
from castle.cms.pwexpiry.utils import days_since_event
from castle.cms.utils import get_managers, send_email, strings_differ
from DateTime import DateTime
from plone import api
from plone.protect.authenticator import createToken
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.PasswordResetTool.PasswordResetTool import (ExpiredRequestError,
                                                          InvalidRequestError)
from ZODB.POSException import ConnectionStateError
from zope.component import getMultiAdapter, getUtility
from zope.component.interfaces import ComponentLookupError
from zope.i18n import translate
from zope.interface import alsoProvides, implements


class SecureLoginView(BrowserView):
    implements(ISecureLoginAllowedView)

    def __init__(self, context, request):
        super(SecureLoginView, self).__init__(context, request)
        self.auth = self.authenticator = getMultiAdapter(
            (context, request), IAuthenticator)

    def __call__(self):
        api_method = self.request.form.get('apiMethod')
        if api_method:
            self.request.response.setHeader('Content-type', 'application/json')

        if api_method == 'send_authorization':
            return self.send_authorization()
        if api_method == 'authorize_code':
            return self.authorize_code()
        if api_method == 'login':
            return self.login()
        if api_method == 'set_password':
            return self.set_password()
        if api_method == 'request_country_exception':
            return self.request_country_exception()
        if api_method == 'reset_password':
            return self.reset_password()

        self.request.response.setHeader('X-Theme-Applied', True)
        return self.index()

    @property
    def username(self):
        return self.request.form.get('username')

    def get_country_header(self):
        return (
            self.request.get_header('Cf-Ipcountry') or
            self.request.get_header('Country'))

    def request_country_exception(self):
        # re-check login...
        # verify we get to country block again
        try:
            self.auth.authenticate(
                username=self.username,
                password=self.request.form.get('password'),
                country=self.get_country_header())
            return json.dumps({
                'success': False,
                'message': 'Error authenticating request',
                'messageType': 'error'
            })
        except authentication.AuthenticationCountryBlocked:
            pass

        req_country = self.get_country_header()
        user = api.user.get(username=self.username)
        data = self.auth.issue_country_exception(user, req_country)

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
<li><b>User agent</b>: {user_agent}</li>
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

    def set_password(self):
        # 1. Authenticate user
        authorized, user = self.auth.authenticate(
            username=self.username,
            password=self.request.form.get('existing_password'),
            country=self.get_country_header(),
            login=False)

        if not user or not authorized:
            return json.dumps({
                'success': False,
                'message': 'Existing credentials did not match'
            })

        # 2. Set password
        newpw = self.request.form.get('new_password')

        registration = getToolByName(self.context, 'portal_registration')
        err_str = registration.testPasswordValidity(newpw)

        if err_str is not None:
            return json.dumps({
                'success': False,
                'message': translate(err_str)
            })

        mtool = api.portal.get_tool('portal_membership')
        member = mtool.getMemberById(user.getId())

        self.auth.change_password(member, newpw)

        self.auth.authenticate(
            username=self.username,
            password=newpw,
            country=self.get_country_header(),
            login=True)

        return json.dumps({
            'success': True
        })

    '''
    this function is here since the current
    login form doesn't use PAS for validation.
    '''
    def pwexpiry(self, user):
        pwexpiry_enabled = api.portal.get_registry_record('plone.pwexpiry_enabled', default=False)
        validity_period = api.portal.get_registry_record('plone.pwexpiry_validity_period', default=0)
        if pwexpiry_enabled and validity_period > 0:
            whitelist = api.portal.get_registry_record('plone.pwexpiry_whitelisted_users', default=[])
            whitelisted = whitelist and user.getId() in whitelist
            if not whitelisted:
                password_date = user.getProperty(
                    'password_date',
                    '2000/01/01'
                )
                current_time = DateTime()
                editableUser = api.user.get(username=user.getId())
                if password_date.strftime('%Y/%m/%d') != '2000/01/01':
                    since_last_pw_reset = days_since_event(
                        password_date.asdatetime(),
                        current_time.asdatetime()
                    )

                    '''
                    depending how you intepret the setting, it might make
                    more sense to check if it's <= 0 instead.
                    Leaving as strictly LT for now.
                    '''
                    if validity_period - since_last_pw_reset < 0:
                        # Password has expired
                        editableUser.setMemberProperties({
                            'reset_password_required': True,
                            'reset_password_time': time.time()
                        })
                        return True
                else:
                    editableUser.setMemberProperties({
                        'password_date': current_time
                    })
        return False

    def login(self):
        # double check auth code first
        code = self.request.form.get('code')
        if (self.auth.two_factor_enabled and not
                self.auth.authorize_2factor(self.username, code, 5 * 60)):
            return json.dumps({
                'success': False,
                'message': 'Login failed for username and password.'
            })

        try:
            if hasattr(self.context, 'portal_registry'):
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
            authorized, user = self.auth.authenticate(
                username=self.username,
                password=self.request.form.get('password'),
                country=self.get_country_header(),
                login=False)
            if authorized:
                reset_password = user.getProperty(
                    'reset_password_required', False)

                if not self.auth.is_zope_root:
                    reset_password = reset_password | self.pwexpiry(user)

                resp = {
                    'success': True,
                    'resetpassword': reset_password
                }
                if reset_password:
                    resp['message'] = 'Your password has expired.'
                else:
                    authorized, user = self.auth.authenticate(
                        username=self.username,
                        password=self.request.form.get('password'),
                        country=self.get_country_header(),
                        login=True)
                try:
                    with api.env.adopt_user(user=user):
                        resp['authenticator'] = createToken()
                        return json.dumps(resp)
                except Exception:
                    resp['authenticator'] = createToken()
                    return json.dumps(resp)
            else:
                return json.dumps({
                    'success': False,
                    'message': 'Login failed for username and password.'
                })
        except authentication.AuthenticationMaxedLoginAttempts:
            return json.dumps({
                'success': False,
                'message': 'You have reached the have number of login attempts '
                           'for a period.'
            })
        except authentication.AuthenticationUserDisabled:
            return json.dumps({
                'success': False,
                'message': 'User is disabled.'
            })
        except authentication.AuthenticationCountryBlocked:
            return json.dumps({
                'success': True,
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

    def authorize_code(self):
        code = self.request.form.get('code')
        if self.authenticator.authorize_2factor(self.username, code):
            return json.dumps({
                'success': True,
                'message': 'Authorization code verified.'
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
        return json.dumps({
            'success': True,
            'message': 'Authorization code sent to provided username if '
                       'username exists.'
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

    def reset_password(self):
        pw_tool = api.portal.get_tool('portal_password_reset')
        registration = api.portal.get_tool('portal_registration')
        userid = self.request.form.get('userid')
        randomstring = self.request.form.get('code')
        password = self.request.form.get('password')

        err_str = registration.testPasswordValidity(password)
        if err_str is not None:
            return json.dumps({
                'success': False,
                'message': translate(err_str)
            })

        alsoProvides(self.request, IDisableCSRFProtection)
        try:
            pw_tool.resetPassword(userid, randomstring, password)
        except ExpiredRequestError:
            return json.dumps({
                'success': False,
                'message': 'Password reset request has expired'
            })
        except (InvalidRequestError, RuntimeError):
            return json.dumps({
                'success': False,
                'message': 'Password reset request is invalid'
            })

        return json.dumps({
            'success': True,
            'message': 'Password reset successfully'
        })

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

        data = {
            'supportedAuthSchemes': self.authenticator.get_supported_auth_schemes(),
            'twoFactorEnabled': self.authenticator.two_factor_enabled,
            'apiEndpoint': '{}/@@secure-login'.format(site_url),
            'successUrl': success_url
        }
        try:
            data['authenticator'] = createToken()
        except ConnectionStateError:
            # zope root related issue here...
            pass

        username = None
        pwreset = self.request.form.get('pwreset') == 'true'
        if pwreset:
            try:
                user = api.user.get(self.request.form.get('userid'))
                username = user.getUserName()
                data.update({
                    'passwordReset': pwreset,
                    'username': username,
                    'code': self.request.form.get('code'),
                    'userid': self.request.form.get('userid')
                })
            except Exception:
                pwreset = False
        return json.dumps(data)


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
<li><b>User agent</b>: {user_agent}</li>
</ul>

<p>You have 12 hours to use this granted login exception.</p>
'''.format(**email_data)
        send_email(email, email_subject, html=email_html)
