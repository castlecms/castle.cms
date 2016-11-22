# -*- coding: utf-8 -*-
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms import toolbar

import unittest
import json


class TestToolbar(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        api.content.create(
            type='Folder',
            id='folder',
            container=self.portal)

    def test_toolbar_renders_items(self):
        tlb = toolbar.Toolbar(self.portal, self.request)
        result = json.loads(tlb())
        self.assertTrue('main_menu' in result)
        self.assertEqual(result['main_menu'][0]['title'], 'View Page')

    def test_addable_types(self):
        tlb = toolbar.Toolbar(self.portal.folder, self.request)
        result = json.loads(tlb())
        self.assertTrue('add' in result)

    def test_breadcrumbs(self):
        tlb = toolbar.Toolbar(self.portal.folder, self.request)
        result = json.loads(tlb())
        self.assertEqual(result['breadcrumbs'][-1]['Title'], 'folder')
