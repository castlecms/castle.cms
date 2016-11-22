# -*- coding: utf-8 -*-
from castle.cms.browser.utils import Utils
from castle.cms import utils
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from OFS.CopySupport import _cb_encode
from ZODB.POSException import ConflictError

import unittest


class TestUtils(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.utils = Utils(self.portal, self.request)

    def test_main_links(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        if 'front-page' not in self.portal:
            api.content.create(type='Document', id='front-page',
                               container=self.portal)

            self.portal.setDefaultPage('front-page')
        data = self.utils.get_main_links()
        self.assertEquals(data['selected_portal_tab'], 'index_html')
        self.assertEquals(len(data['portal_tabs']), 1)

    def test_truncate_text(self):
        self.assertEqual(
            len(utils.truncate_text('foo bar foo bar', 2).split(' ')),
            2)

    def test_truncate_text_with_html(self):
        result = utils.truncate_text('foo <b>bar</b> <span>foo bar</span>', 2)
        self.assertEqual('foo <b>bar&hellip;</b>', result)

    def test_random_functions(self):
        self.assertEqual(len(utils.get_random_string(15)), 15)
        self.assertEqual(len(utils.make_random_key(15)), 15)

    def test_get_paste_data(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        api.content.create(type='Document', id='newpage',
                           container=self.portal)
        cp = (0, [
            ('', 'plone', 'newpage')
        ])
        cp = _cb_encode(cp)
        self.request['__cp'] = cp

        data = utils.get_paste_data(self.request)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['op'], 0)
        self.assertEqual(data['paths'], ['/plone/newpage'])

    def test_recursive_create_path(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        folder = utils.recursive_create_path(self.portal, '/foo/bar/blah')
        self.assertEqual(
            '/'.join(folder.getPhysicalPath()),
            '/plone/foo/bar/blah'
        )

    def test_retriable(self):
        count = []

        @utils.retriable(reraise=False)
        def dosomething():
            count.append(1)
            raise ConflictError()

        dosomething()
        self.assertEqual(len(count), 3)
