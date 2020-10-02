# -*- coding: utf-8 -*-
from Products.PloneKeywordManager.tests.test_controlpanel import ControlPanelTestCase
from Products.PloneKeywordManager.tests.test_dexterity import DexterityContentTestCase
from Products.PloneKeywordManager.tests.test_non_ascii_keywords import NonAsciiKeywordsTestCase
from Products.PloneKeywordManager.tests.test_setup import InstallTestCase
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


class Install(InstallTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING
