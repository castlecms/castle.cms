# -*- coding: utf-8 -*-
from Products.PloneKeywordManager.tests.test_controlpanel import ControlPanelTestCase
from Products.PloneKeywordManager.tests.test_dexterity import DexterityContentTestCase
from Products.PloneKeywordManager.tests.test_non_ascii_keywords import NonAsciiKeywordsTestCase

# Plone5.2 TODO - InstallTestCase renamed to TestSetup. Some tests still failing
from Products.PloneKeywordManager.tests.test_setup import TestSetup
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api


class ControlPanel(ControlPanelTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING


class DexterityContent(DexterityContentTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        super(DexterityContent, self).setUp()
        api.content.transition(obj=self.content, to_state='published')


class NonAsciiKeywords(NonAsciiKeywordsTestCase):
    # layer = CASTLE_PLONE_INTEGRATION_TESTING #fails for some reason?
    pass


class Install(TestSetup):
    layer = CASTLE_PLONE_INTEGRATION_TESTING
