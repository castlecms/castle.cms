# -*- coding: utf-8 -*-
from Products.PloneKeywordManager.tests.test_controlpanel import ControlPanelTestCase
from Products.PloneKeywordManager.tests.test_dexterity import DexterityContentTestCase
from Products.PloneKeywordManager.tests.test_non_ascii_keywords import NonAsciiKeywordsTestCase
from Products.PloneKeywordManager.tests.test_setup import InstallTestCase
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING


class ControlPanel(ControlPanelTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING


class DexterityContent(DexterityContentTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING


class NonAsciiKeywords(NonAsciiKeywordsTestCase):
    # layer = CASTLE_PLONE_INTEGRATION_TESTING #fails for some reason?
    pass


class Install(InstallTestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING
