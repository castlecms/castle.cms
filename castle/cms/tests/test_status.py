from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

import unittest

from castle.cms.browser import controlpanel
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING


class StatusTest(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_status_control_panel_exists(self):
        view = dir(controlpanel)
        string = 'status'
        if string in view:
            self.assertTrue(True, msg='None')
        else:
            self.assertTrue(False, msg='can``t find status control panel')
