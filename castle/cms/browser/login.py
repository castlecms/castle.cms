from castle.cms import authentication
from castle.cms import cache
from castle.cms import texting
from castle.cms.interfaces import IAuthenticator
from castle.cms.interfaces import ISecureLoginAllowedView
from castle.cms.interfaces import ISiteSchema
from castle.cms.utils import get_managers
from castle.cms.utils import send_email
from castle.cms.utils import strings_differ
from plone import api
from plone.protect.authenticator import createToken
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from Products.PasswordResetTool.PasswordResetTool import ExpiredRequestError
from Products.PasswordResetTool.PasswordResetTool import InvalidRequestError
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from zope.interface import alsoProvides
from zope.interface import implements

import json
import time


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
        # 1. only set password for logged in user...
        if api.user.is_anonymous():
            return json.dumps({
                'success': False,
                'message': 'Need to be logged in to reset password'
            })

        acl_users = self.get_tool('acl_users')

        # 2. double check existing password
        user = acl_users.authenticate(
            self.username, self.request.form.get('existing_password'),
            self.request)

        if not user:
            return json.dumps({
                'success': False,
                'message': 'Existing password did not match'
            })

        if user.getId() != api.user.get_current().getId():
            return json.dumps({
                'success': False,
                'message': 'Error resetting'
            })

        # 3. finally, set password
        newpw = self.request.form.get('new_password')

        mtool = api.portal.get_tool('portal_membership')
        member = mtool.getMemberById(user.getId())

        self.auth.change_password(member, newpw)

        return json.dumps({
            'success': True
        })

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
            authorized, user = self.auth.authenticate(
                username=self.username,
                password=self.request.form.get('password'),
                country=self.get_country_header())
            if authorized:
                reset_password = user.getProperty(
                    'reset_password_required', False)

                resp = {
                    'success': True,
                    'resetpassword': reset_password
                }
                try:
                    with api.env.adopt_user(user=user):
                        resp['authenticator'] = createToken()
                        return json.dumps(resp)
                except:
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
        userid = self.request.form.get('userid')
        randomstring = self.request.form.get('code')
        password = self.request.form.get('password')
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
        site_url = self.context.absolute_url()
        data = {
            'supportedAuthSchemes': self.authenticator.get_supported_auth_schemes(),
            'twoFactorEnabled': self.authenticator.two_factor_enabled,
            'apiEndpoint': '{}/@@secure-login'.format(site_url),
            'successUrl': site_url,
            'authenticator': createToken()
        }

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
            except:
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
            except:
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
