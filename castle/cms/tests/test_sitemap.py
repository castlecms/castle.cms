# -*- coding: utf-8 -*-
import unittest

from castle.cms.browser.site.sitemap import SiteMapView
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles


class TestSiteMap(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        if 'front-page' not in self.portal:
            self.page = api.content.create(type='Document', id='front-page',
                                           container=self.portal)
            self.portal.setDefaultPage('front-page')

    def test_get_objects(self):
        view = SiteMapView(self.portal, self.request)
        paths = [o for o in view.objects()]
        self.assertEquals(paths[0]['loc'], self.portal.absolute_url())

    def test_no_private_content(self):
        folder = api.content.create(
            type='Folder',
            id='test-folder',
            container=self.portal
        )
        page = api.content.create(
            type='Document',
            id='test-page',
            container=folder
        )
        api.content.transition(obj=page, to_state='published')
        view = SiteMapView(self.portal, self.request)
        locations = [object['loc'] for object in view.objects()]
        self.assertFalse('http://nohost/plone/test-folder' in locations)
        self.assertFalse('http://nohost/plone/test-folder/test-page' in locations)
        api.content.transition(obj=folder, to_state='published')
        locations = [object['loc'] for object in view.objects()]
        self.assertTrue('http://nohost/plone/test-folder' in locations)
        self.assertTrue('http://nohost/plone/test-folder/test-page' in locations)
