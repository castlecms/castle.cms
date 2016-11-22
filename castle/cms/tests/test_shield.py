# -*- coding: utf-8 -*-
from castle.cms import constants
from castle.cms import shield
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import TEST_USER_NAME
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import queryUtility

import unittest


SHIELD = constants.SHIELD


class TestTwoFactor(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def test_raises_redirect_exception_when_shield_active(self):
        logout()
        registry = queryUtility(IRegistry)
        registry['plone.login_shield_setting'] = SHIELD.ALL
        self.request.PARENTS = [self.portal]
        self.assertRaises(Redirect, shield.protect, self.request)

    def test_not_raises_redirect_exception_when_shield_not_active(self):
        logout()
        registry = queryUtility(IRegistry)
        registry['plone.login_shield_setting'] = SHIELD.NONE
        self.request.PARENTS = [self.portal]
        shield.protect(self.request)

    def test_not_raises_redirect_exception_when_shield_active_and_logged_in(self):
        login(self.portal, TEST_USER_NAME)
        registry = queryUtility(IRegistry)
        registry['plone.login_shield_setting'] = SHIELD.ALL
        self.request.PARENTS = [self.portal]
        shield.protect(self.request)
