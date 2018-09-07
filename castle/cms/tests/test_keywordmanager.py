from Products.PloneKeywordManager.tests.test_controlpanel import ControlPanelTestCase
from Products.PloneKeywordManager.tests.test_dexterity import DexterityContentTestCase
from Products.PloneKeywordManager.tests.test_non_ascii_keywords import NonAsciiKeywordsTestCase
from Products.PloneKeywordManager.tests.test_setup import InstallTestCase

class ControlPanel(ControlPanelTestCase):
    pass

class DexterityContent(DexterityContentTestCase):
    pass

class NonAsciiKeywords(NonAsciiKeywordsTestCase):
    pass

class Install(InstallTestCase):
    pass
