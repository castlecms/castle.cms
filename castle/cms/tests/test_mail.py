from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
import unittest

from castle.cms.constants import ALL_SUBSCRIBERS
from castle.cms.constants import ALL_USERS
from castle.cms import subscribe
from castle.cms.utils.mail import send_email
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING

import plone.api as api


class StatusTest(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.mailhost = getattr(self.portal, 'MailHost', None)
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def create_subscribers(self, subscriber_count=0):
        for index in range(subscriber_count):
            email = 'subscriber{}@fake.com'.format(index)
            data = subscribe.register(email, {})
            subscribe.confirm(email, data['code'])
        subscribers = list(subscribe.all())
        self.assertEquals(len(subscribers), subscriber_count)

    def create_users(self, user_count=0, remove_test_user=True):
        for index in range(user_count):
            email = 'user{}@fake.com'.format(index)
            username = 'fake.user{}'.format(index)
            api.user.create(
                email=email,
                username=username,
            )
        if remove_test_user:
            api.user.delete(
                user=api.user.get(userid=TEST_USER_ID)
            )
        self.assertEqual(
            len(api.user.get_users()),
            user_count,
        )

    @property
    def mail_messages(self):
        messages = getattr(self.mailhost, 'messages', None)
        self.assertIsNotNone(messages)
        return messages or []

    def assertMailCount(self, count):
        self.assertEquals(
            count,
            len(self.mail_messages),
        )

    def test_send_mail_without_recipients(self):
        try:
            send_email()
            self.assertMailCount(0)
        except Exception:
            assert False, 'send_mail raised an exception but shouldn\'t have'

    def test_send_email(self):
        send_email(
            recipients=['email@fake.com'],
            subject='Test Email',
            text='body text',
            html='<p>body html</p>',
            sender='Testing',
        )
        self.assertMailCount(1)
        message = self.mail_messages[0]
        self.assertIn('Subject: Test Email', message)
        self.assertIn('From: Testing', message)
        self.assertIn('To: email@fake.com', message)
        self.assertIn('body text', message)
        self.assertIn('<p>body html</p>', message)

    def test_send_email_to_subscribers(self):
        self.create_subscribers(3)
        send_email(recipients=ALL_SUBSCRIBERS)
        self.assertMailCount(3)
        for message in self.mail_messages:
            self.assertTrue(
                'To: subscriber0@fake.com' in message or
                'To: subscriber1@fake.com' in message or
                'To: subscriber2@fake.com' in message
            )

    def test_recipients_can_be_string_or_list(self):
        send_email(recipients=['email@fake.com'])
        send_email(recipients='email@fake.com')
        self.assertMailCount(2)
        for message in self.mail_messages:
            self.assertIn('To: email@fake.com', message)

    def test_send_to_all_users(self):
        self.create_users(4, True)
        send_email(recipients=ALL_USERS)
        self.assertMailCount(4)
        for message in self.mail_messages:
            self.assertTrue(
                'To: user0@fake.com' in message or
                'To: user1@fake.com' in message or
                'To: user2@fake.com' in message or
                'To: user3@fake.com' in message
            )

    def test_send_to_users_and_user_groups(self):
        self.create_users(1, True)
        self.create_subscribers(1)
        send_email(recipients=[ALL_USERS, ALL_SUBSCRIBERS, 'non_user@fake.com'])
        self.assertMailCount(3)
        for message in self.mail_messages:
            self.assertTrue(
                'To: user0@fake.com' in message or
                'To: subscriber0@fake.com' in message or
                'To: non_user@fake.com' in message
            )

    def test_email_to_address_formatting_without_username(self):
        self.create_users(1, True)
        user = api.user.get_users()[0]
        full_name = user.getProperty('fullname')
        self.assertEqual(full_name, '')

        send_email(recipients='user0@fake.com')
        message = self.mail_messages[0]
        self.assertIn('To: user0@fake.com', message)
        self.assertNotIn('To: User 0<user0@fake.com>', message)

    def test_email_to_address_formatting_with_username(self):
        self.create_users(1, True)
        user = api.user.get_users()[0]
        user.setMemberProperties({'fullname': 'User 0'})
        full_name = api.user.get_users()[0].getProperty('fullname')
        self.assertEqual(full_name, 'User 0')

        send_email(recipients='user0@fake.com')
        message = self.mail_messages[0]
        self.assertIn('To: User 0<user0@fake.com>', message)
        self.assertNotIn('To: user0@fake.com', message)

    def test_no_duplicate_emails(self):
        self.create_users(1, True)
        send_email(recipients=[ALL_USERS, 'user0@fake.com'])
        self.assertMailCount(1)
