# -*- coding: utf-8 -*-
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from Products.PloneKeywordManager.tests.test_controlpanel import ControlPanelTestCase
from Products.PloneKeywordManager.tests.test_dexterity import DexterityContentTestCase
from Products.PloneKeywordManager.tests.test_non_ascii_keywords import NonAsciiKeywordsTestCase
from Products.PloneKeywordManager.tests.test_setup import TestSetup
from Products.PloneKeywordManager.tests.test_setup import TestUninstall


class ControlPanel(ControlPanelTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING


class DexterityContent(DexterityContentTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING


class NonAsciiKeywords(NonAsciiKeywordsTestCase):
    # layer = CASTLE_PLONE_INTEGRATION_TESTING #fails for some reason?
    pass


class Setup(TestSetup):
    layer = CASTLE_PLONE_INTEGRATION_TESTING


class Uninstall(TestUninstall):
    layer = CASTLE_PLONE_INTEGRATION_TESTING
