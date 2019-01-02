# -*- coding: utf-8 -*-
import json
import time
import unittest

import responses
from AccessControl import AuthEncoding
from castle.cms import cache
from castle.cms import constants
from castle.cms import security
from castle.cms.browser.security.login import SecureLoginView
from castle.cms.interfaces import IAuthenticator
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from DateTime import DateTime
from plone import api
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import login
from plone.app.testing import logout
from plone.protect.authenticator import createToken
from plone.registry.interfaces import IRegistry
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility


try:
    import argon2
except ImportError:
    argon2 = None


SHIELD = constants.SHIELD
TEST_USER_NEW_PASSWORD = TEST_USER_PASSWORD + '123'


class TestTwoFactor(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        portal_memberdata = self.portal.portal_memberdata
        if not portal_memberdata.hasProperty("reset_password_required"):
            portal_memberdata.manage_addProperty(
                id="reset_password_required", value=False, type="boolean")
            portal_memberdata.manage_addProperty(
                id="reset_password_time", value=time.time(), type="float")
        logout()

    def test_authentication_adapter(self):
        getMultiAdapter((self.portal, self.request), IAuthenticator)

    def test_get_options(self):
        registry = queryUtility(IRegistry)
        registry['plone.two_factor_enabled'] = True
        registry['castle.plivo_auth_id'] = u'foobar'
        view = SecureLoginView(self.portal, self.request)
        opts = json.loads(view.options())
        self.assertTrue(opts['twoFactorEnabled'])
        self.assertEquals(len(opts['supportedAuthSchemes']), 2)

    def test_success_url_is_dashboard(self):
        registry = queryUtility(IRegistry)
        registry['plone.two_factor_enabled'] = True
        registry['castle.plivo_auth_id'] = u'foobar'
        view = SecureLoginView(self.portal, self.request)
        opts = json.loads(view.options())
        self.assertTrue('@@dashboard' in opts['successUrl'])

    def test_success_url_uses_came_from(self):
        registry = queryUtility(IRegistry)
        registry['plone.two_factor_enabled'] = True
        registry['castle.plivo_auth_id'] = u'foobar'
        self.request.form.update({
            'came_from': self.portal.absolute_url() + '/foobar'
        })
        view = SecureLoginView(self.portal, self.request)
        opts = json.loads(view.options())
        self.assertTrue('/foobar' in opts['successUrl'])

    @responses.activate
    def test_send_text_message_with_code(self):
        responses.add(
            responses.POST,
            "https://api.plivo.com/v1/Account/foobar_auth_id/Message/",
            body='{"success": true}',
            content_type="application/json")

        registry = queryUtility(IRegistry)
        registry['castle.plivo_auth_id'] = u'foobar_auth_id'
        registry['castle.plivo_auth_token'] = u'foobar_auth_token'
        registry['castle.plivo_phone_number'] = u'15555555555'

        user = api.user.get(username=TEST_USER_NAME)
        user.setMemberProperties(mapping={'phone_number': '19999999999', })
        self.request.form.update({
            'apiMethod': 'send_authorization',
            'authType': 'sms',
            'username': TEST_USER_NAME
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])
        self.assertEquals(len(responses.calls), 1)
        text_body = json.loads(responses.calls[0].request.body)
        self.assertTrue('code:' in text_body['text'])
        self.assertEquals(text_body['dst'], '19999999999')
        self.assertEquals(text_body['src'], '15555555555')

    def test_send_email_with_code(self):
        self.request.form.update({
            'apiMethod': 'send_authorization',
            'authType': 'email',
            'username': TEST_USER_NAME
        })
        user = api.user.get(username=TEST_USER_NAME)
        user.setMemberProperties(mapping={'email': 'foo@bar.com', })

        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])

        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 1)

    def test_authorize_code_succeeds(self):
        self.request.form.update({
            'apiMethod': 'authorize_code',
            'username': TEST_USER_NAME
        })
        view = SecureLoginView(self.portal, self.request)
        code = view.auth.issue_2factor_code(TEST_USER_NAME)
        self.request.form.update({
            'code': code
        })
        result = json.loads(view())
        self.assertTrue(result['success'])

    def test_authorize_code_fails(self):
        self.request.form.update({
            'apiMethod': 'authorize_code',
            'username': TEST_USER_NAME,
            'code': 'foobar'
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_authorize_code_required_for_login(self):
        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = True
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_login_success(self):
        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = True
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        code = view.auth.issue_2factor_code(TEST_USER_NAME)
        self.request.form.update({
            'code': code
        })
        result = json.loads(view())
        self.assertTrue(result['success'])

    def test_login_failure(self):
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': 'foobar'
        })
        view = SecureLoginView(self.portal, self.request)
        code = view.auth.issue_2factor_code(TEST_USER_NAME)
        self.request.form.update({
            'code': code
        })
        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_login_success_without_two_factor(self):
        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = False
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])

    def test_authorize_code_does_not_work_out_of_time(self):
        self.request.form.update({
            'apiMethod': 'authorize_code',
            'username': TEST_USER_NAME
        })
        view = SecureLoginView(self.portal, self.request)
        code = view.auth.issue_2factor_code(TEST_USER_NAME)
        self.request.form.update({
            'code': code
        })

        # set the code back
        cache_key = view.auth.get_2factor_code_key(TEST_USER_NAME)
        code_data = cache.get(cache_key)
        code_data['timestamp'] -= (5 * 60) + 1
        cache.set(cache_key, code_data)

        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_password_reset_expired_does_not_allow_login(self):
        # set reset stuff...
        user = api.user.get(username=TEST_USER_NAME)
        user.setMemberProperties(mapping={
            'reset_password_required': True,
            'reset_password_time': time.time() - (48 * 60 * 60)
        })

        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = False
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        self.request.method = self.request.REQUEST_METHOD = 'POST'

        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_password_reset_after_login(self):
        # set reset stuff...
        user = api.user.get(username=TEST_USER_NAME)
        user.setMemberProperties(mapping={
            'reset_password_required': True,
            'reset_password_time': time.time()
        })

        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = False
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD,
            '_authenticator': createToken()
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])
        self.assertTrue(result['resetpassword'])

    def test_password_reset(self):
        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = False
        login(self.portal, TEST_USER_NAME)
        self.request.form.update({
            'apiMethod': 'set_password',
            'username': TEST_USER_NAME,
            'existing_password': TEST_USER_PASSWORD,
            'new_password': TEST_USER_NEW_PASSWORD,
            '_authenticator': createToken()
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])

    def test_password_reset_password_does_not_match(self):
        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = False
        login(self.portal, TEST_USER_NAME)
        self.request.form.update({
            'apiMethod': 'set_password',
            'username': TEST_USER_NAME,
            'existing_password': 'foobar',
            'new_password': 'foobar2',
            '_authenticator': createToken()
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_country_code_not_allowed(self):
        registry = getUtility(IRegistry)
        registry['plone.two_factor_enabled'] = False
        registry['plone.restrict_logins_to_countries'] = (u'US',)
        self.request.environ['HTTP_CF_IPCOUNTRY'] = 'AF'
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])
        self.assertTrue(result['countryBlocked'])


class TestEnforceBackendEditingUrl(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        logout()

    def test_setting_disabled(self):
        api.portal.set_registry_record(
            name='plone.only_allow_login_to_backend_urls',
            value=False
        )
        api.portal.set_registry_record(
            name='plone.backend_url',
            value=(unicode(''),)
        )
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])

    def test_setting_enabled_bad_url(self):
        api.portal.set_registry_record(
            name='plone.only_allow_login_to_backend_urls',
            value=True
        )
        api.portal.set_registry_record(
            name='plone.backend_url',
            value=(unicode(''),)
        )
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_setting_enabled_good_url(self):
        api.portal.set_registry_record(
            name='plone.only_allow_login_to_backend_urls',
            value=True
        )
        api.portal.set_registry_record(
            name='plone.backend_url',
            value=(
                unicode('http://dummydomain/castle'),
                unicode('http://nohost/plone'),
                unicode('http://vpn.example.com')
            )
        )
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])

    def test_setting_enabled_no_urls(self):
        api.portal.set_registry_record(
            name='plone.only_allow_login_to_backend_urls',
            value=True
        )
        api.portal.set_registry_record(
            name='plone.backend_url',
            value=()
        )
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])


class TestPasswordLength(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)

    def test_short_password(self):
        shortpass = 'pass'
        self.request.form.update({
            'apiMethod': 'set_password',
            'username': TEST_USER_NAME,
            'existing_password': TEST_USER_PASSWORD,
            'new_password': shortpass
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['success'])

    def test_long_password(self):
        longpass = 'N1C3P@$$w0rd'
        self.request.form.update({
            'apiMethod': 'set_password',
            'username': TEST_USER_NAME,
            'existing_password': TEST_USER_PASSWORD,
            'new_password': longpass
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])


class TestPwexpiry(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        api.portal.set_registry_record(
            name='plone.pwexpiry_enabled',
            value=True
        )
        api.portal.set_registry_record(
            name='plone.pwexpiry_whitelisted_users',
            value=[]
        )
        logout()

    def test_initial_login(self):
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])
        self.assertFalse(result['resetpassword'])

    def test_expired_login(self):
        editableUser = api.user.get(username=TEST_USER_NAME)
        editableUser.setMemberProperties({
            'password_date': DateTime('01/10/2011')
        })
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['resetpassword'])

    def test_whitelist(self):
        editableUser = api.user.get(username=TEST_USER_NAME)
        editableUser.setMemberProperties({
            'password_date': DateTime('01/10/2011')
        })
        api.portal.set_registry_record(
            name='plone.pwexpiry_whitelisted_users',
            value=[editableUser.getId().decode('utf-8')]
        )
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': TEST_USER_PASSWORD
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['resetpassword'])

    def test_password_history(self):
        pass1 = 'N1C3P@$$w0rd'
        pass2 = 'P@$$w0rd2018'
        editableUser = api.user.get(username=TEST_USER_NAME)
        editableUser.setMemberProperties({
            'password_date': DateTime('01/10/2011')
        })
        login(self.portal, TEST_USER_NAME)

        # -----Change password-----
        self.request.form.update({
            'apiMethod': 'set_password',
            'username': TEST_USER_NAME,
            'existing_password': TEST_USER_PASSWORD,
            'new_password': pass1
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])
        logout()

        # -----Try logging in with new password-----
        self.request.form.update({
            'apiMethod': 'login',
            'username': TEST_USER_NAME,
            'password': pass1
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['resetpassword'])

        # -----Change password again-----
        login(self.portal, TEST_USER_NAME)
        self.request.form.update({
            'apiMethod': 'set_password',
            'username': TEST_USER_NAME,
            'existing_password': pass1,
            'new_password': pass2
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertTrue(result['success'])

        # -----Try to change password back-----
        self.request.form.update({
            'apiMethod': 'set_password',
            'username': TEST_USER_NAME,
            'existing_password': pass2,
            'new_password': pass1
        })
        view = SecureLoginView(self.portal, self.request)
        result = json.loads(view())
        self.assertFalse(result['success'])


if argon2 is not None:
    class TestArgon2(unittest.TestCase):
        def test_registered(self):
            self.assertTrue('argon2' in [s[0] for s in AuthEncoding._schemes])

        def test_encrypt(self):
            scheme = security.Argon2Scheme()
            encrypted = scheme.encrypt('foobar')
            self.assertTrue(scheme.validate(encrypted, 'foobar'))

        def test_argon_is_used_by_default(self):
            encrypted = AuthEncoding.pw_encrypt('foobar')
            self.assertTrue('{argon2}' in encrypted)
            self.assertTrue(AuthEncoding.pw_validate(encrypted, 'foobar'))
