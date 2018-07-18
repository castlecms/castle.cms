from castle.cms import authentication
from castle.cms import cache
from castle.cms import texting
from castle.cms.interfaces import IAuthenticator
from castle.cms.interfaces import ISecureLoginAllowedView
from castle.cms.interfaces import ISiteSchema
from castle.cms.utils import get_managers
from castle.cms.utils import send_email
from castle.cms.utils import strings_differ
from castle.cms.utils import days_since_event
from plone import api
from plone.protect.authenticator import createToken
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import ISiteRoot
from Products.Five import BrowserView
from Products.PasswordResetTool.PasswordResetTool import ExpiredRequestError
from Products.PasswordResetTool.PasswordResetTool import InvalidRequestError
from ZODB.POSException import ConnectionStateError
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.interfaces import ComponentLookupError
from zope.interface import alsoProvides
from zope.interface import implements
from AccessControl import AuthEncoding
from DateTime import DateTime
import json
import time

'''TODO: Remove log messages.'''
import logging
logger = logging.getLogger("Plone")

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

    def pwexpiry_check_history(self,user,password):
        registry = self.get_registry()
        pwexpiry_enabled = registry['plone.pwexpiry_enabled']
        max_history_pws = registry['plone.pwexpiry_password_history_size']
        whitelisted = registry['plone.pwexpiry_whitelisted_users']
        if whitelisted and user.getId() in whitelisted:
            return False
        if password is not None and \
        pwexpiry_enabled and \
        max_history_pws > 0:
            pw_history = user.getProperty(
                'password_history',
                []
            )
            for old_pw in pw_history[-max_history_pws:]:
                if AuthEncoding.pw_validate(old_pw, str(password)):
                    return True
        return False

    def pwexpiry_add_history(self,user,password):
        registry = self.get_registry()
        pwexpiry_enabled = registry['plone.pwexpiry_enabled']
        max_history_pws = registry['plone.pwexpiry_password_history_size']
        if password is not None and \
        max_history_pws > 0:
            enc_pw = password
            if not AuthEncoding.is_encrypted(enc_pw):
                enc_pw = AuthEncoding.pw_encrypt(enc_pw)
            pw_history = list(user.getProperty(
                'password_history',
                []
            ))
            pw_history.append(enc_pw)
            if len(pw_history) > max_history_pws:
                # Truncate the history
                pw_history = pw_history[-max_history_pws:]

            user.setMemberProperties({'password_history': pw_history})

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

        if self.pwexpiry_check_history(member, newpw):
            return json.dumps({
                'success': False,
                'message': 'You\'ve used that password before.'
            })
        member.setMemberProperties({
            'password_date': DateTime()
        })
        self.pwexpiry_add_history(member, newpw)
        self.auth.change_password(member, newpw)

        return json.dumps({
            'success': True
        })

    def pwexpiry(self, user):
        registry = self.get_registry()
        pwexpiry_enabled = registry['plone.pwexpiry_enabled']
        validity_period = registry['plone.pwexpiry_validity_period']
        if pwexpiry_enabled and validity_period > 0:
            whitelist = registry['plone.pwexpiry_whitelisted_users']
            whitelisted = whitelist and user.getId() not in whitelist
            if not whitelisted:
                logger.info('not whitelisted')
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
        else:
            api.user.get(username=user.getUserName()).setMemberProperties({
                'password_date': DateTime(2016,7,11)
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
            authorized, user = self.auth.authenticate(
                username=self.username,
                password=self.request.form.get('password'),
                country=self.get_country_header())
            if authorized:
                reset_password = user.getProperty(
                    'reset_password_required', False)

                if not self.auth.is_zope_root:
                    reset_password = reset_password | self.pwexpiry(user)

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
