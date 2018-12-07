# -*- coding: utf-8 -*-
from castle.cms import subscribe
from castle.cms.browser.controlpanel.announcements import SendEmailSubscribersForm  # noqa
from castle.cms.browser.subscribe import SubscribeForm
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.browser.controlpanel.announcements import ImportSubscribersForm, reg_key
from plone.app.testing import logout
from plone.registry.interfaces import IRegistry
from plone import api
from zope.component import queryUtility

import responses
import transaction
import unittest


class TestSubscribe(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        registry = queryUtility(IRegistry)
        registry['castle.subscriber_categories'] = [u'A', u'B', u'C']

    def test_add_subscriber(self):
        data = subscribe.register('foo@bar.com', {'foo': 'bar'})
        subscribe.confirm('foo@bar.com', data['code'])
        self.assertEquals(len([i for i in subscribe.all()]), 1)

    def test_adds_code(self):
        subscribe.register('foo@bar.com', {'foo': 'bar'})
        item = subscribe.get_subscriber('foo@bar.com')
        self.assertTrue('code' in item)

    def test_get_phone_numbers_empty(self):
        data = subscribe.register('foo@bar.com', {'foo': 'bar'})
        subscribe.confirm('foo@bar.com', data['code'])
        self.assertEquals(len(subscribe.get_phone_numbers()), 0)

    def test_get_phone_numbers(self):
        data = subscribe.register(
            'foo@bar.com', {'foo': 'bar', 'phone_number': '15555555555'})
        subscribe.confirm('foo@bar.com', data['code'])
        subscribe.confirm_phone_number('foo@bar.com', data['code'])
        self.assertEquals(len(subscribe.get_phone_numbers()), 1)

    def test_get_email_address(self):
        data = subscribe.register('foo@bar.com', {'foo': 'bar'})
        subscribe.confirm('foo@bar.com', data['code'])
        self.assertEquals(len(subscribe.get_email_addresses()), 1)

    def test_categories(self):
        data = subscribe.register('foo@bar.com', {'categories': [u'A']})
        subscribe.confirm('foo@bar.com', data['code'])
        user = subscribe.get('foo@bar.com')
        self.assertEquals(user['categories'], [u'A'])
        self.assertFalse(user['categories'] == [])


class TestSubscribeForm(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        registry = queryUtility(IRegistry)
        registry['plone.email_from_address'] = 'foo@bar.com'
        registry['castle.recaptcha_private_key'] = u'foobar'
        registry['castle.recaptcha_public_key'] = u'foobar'
        registry['plone.enable_notification_subscriptions'] = True
        registry['castle.subscriber_categories'] = [u'A', u'B', u'C']

        transaction.commit()

    @responses.activate
    def test_user_subscribes(self):
        responses.add(
            responses.POST, "https://www.google.com/recaptcha/api/siteverify",
            body='{"success": true}',
            content_type="application/json")
        self.request.form.update({
            'form.widgets.name': u'Foobar',
            'form.widgets.email': u'foo@bar.com',
            'g-recaptcha-response': u'foobar',
            'form.buttons.subscribe': 'Subscribe'
        })
        form = SubscribeForm(self.portal, self.request)
        form()
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 1)
        self.assertEquals(len(subscribe.SubscriptionStorage()._data), 1)

    @responses.activate
    def test_invalid_recaptcha(self):
        logout()
        responses.add(
            responses.POST, "https://www.google.com/recaptcha/api/siteverify",
            body='{"success": false}',
            content_type="application/json")
        self.request.form.update({
            'form.widgets.name': u'Foobar',
            'form.widgets.email': u'foo@bar.com',
            'g-recaptcha-response': u'foobar',
            'form.buttons.subscribe': 'Subscribe'
        })
        form = SubscribeForm(self.portal, self.request)
        form()
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 0)
        self.assertEquals(len(subscribe.SubscriptionStorage()._data), 0)

    @responses.activate
    def test_user_exists(self):
        subscribe.register('foo@bar.com', {'foo': 'bar'})
        responses.add(
            responses.POST, "https://www.google.com/recaptcha/api/siteverify",
            body='{"success": true}',
            content_type="application/json")
        self.request.form.update({
            'form.widgets.name': u'Foobar',
            'form.widgets.email': u'foo@bar.com',
            'g-recaptcha-response': u'foobar',
            'form.buttons.subscribe': 'Subscribe'
        })
        form = SubscribeForm(self.portal, self.request)
        form()
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 0)
        self.assertEquals(len(subscribe.SubscriptionStorage()._data), 1)

    @responses.activate
    def _test_category_match(self):
        # XXX fix test(isolation issues)
        subscribe.register('foo@bar.com', {'categories': [u'A']})
        subscriber = subscribe.get('foo@bar.com')
        subscribe.confirm('foo@bar.com', subscriber['code'])
        responses.add(
            responses.POST, "https://www.google.com/recaptcha/api/siteverify",
            body='{"success": true}',
            content_type="application/json")
        self.request.form.update({
            'form.widgets.subject': u'TEST',
            'form.widgets.send_to_categories': u'A',
            'form.widgets.body': 'Words words words',
            'form.widgets.body_plain': 'Words words words',
            'form.buttons.send2': 'Send'
        })
        form = SendEmailSubscribersForm(self.portal, self.request)
        form()
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 1)
        self.assertEquals(len(subscribe.SubscriptionStorage()._data), 1)

    @responses.activate
    def test_category_mismatch(self):
        subscribe.register('foo@bar.com', {'categories': [u'A']})
        subscriber = subscribe.get('foo@bar.com')
        subscribe.confirm('foo@bar.com', subscriber['code'])

        responses.add(
            responses.POST, "https://www.google.com/recaptcha/api/siteverify",
            body='{"success": true}',
            content_type="application/json")
        self.request.form.update({
            'form.widgets.subject': u'TEST',
            'form.widgets.send_to_categories': u'B',
            'form.widgets.body': 'Words words words',
            'form.widgets.body_plain': 'Words words words',
            'form.buttons.send2': 'Send'
        })
        form = SendEmailSubscribersForm(self.portal, self.request)
        form()
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 0)
        self.assertEquals(len(subscribe.SubscriptionStorage()._data), 1)

    def test_confirm(self):
        subscribe.register('foo@bar.com', {'foo': 'bar'})
        subscriber = subscribe.get_subscriber('foo@bar.com')
        self.request.form.update({
            'confirmed_email': u'foo@bar.com',
            'confirmed_code': subscriber['code']
        })
        form = SubscribeForm(self.portal, self.request)
        form()
        self.assertTrue(form.subscribed)
        mailhost = self.portal.MailHost
        self.assertEqual(len(mailhost.messages), 0)
        self.assertEquals(len([i for i in subscribe.all()]), 1)
        subscriber = subscribe.get_subscriber('foo@bar.com')
        self.assertTrue(subscriber['confirmed'])


class TestImport(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def test_import(self):
        self.assertEquals(len(subscribe.SubscriptionStorage()._data), 0)
        self.assertEquals(len(api.portal.get_registry_record(reg_key)), 0)
        self.request.form.update({
            'form.widgets.csv_upload': u'name,email,phone_number,phone_number_confirmed,confirmed,code,created,captcha,categories\nUser,user@example.com,,False,True,,,,"News"', # noqa
            'form.buttons.import': u'Import'
        })
        form = ImportSubscribersForm(self.portal, self.request)
        form()
        self.assertEquals(len(subscribe.SubscriptionStorage()._data), 1)
        self.assertEquals(len(api.portal.get_registry_record(reg_key)), 1)
