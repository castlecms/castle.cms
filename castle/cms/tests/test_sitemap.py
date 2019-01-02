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
        site_size = len(self.portal.portal_catalog())
        view = SiteMapView(self.portal, self.request)
        paths = [o for o in view.objects()]
        self.assertEquals(len(paths), site_size)
        self.assertEquals(paths[0]['loc'], self.portal.absolute_url())
