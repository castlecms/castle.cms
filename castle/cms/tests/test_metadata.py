# -*- coding: utf-8 -*-
from castle.cms.behaviors.location import ILocation
from castle.cms.tiles.metadata import MetaDataTile
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

import unittest


class TestMetadata(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_gives_location(self):
        page = api.content.create(type='Document', title='Foobar', container=self.portal)
        ldata = ILocation(page)
        ldata.locations = [u'Green Bay, WI']

        tile = MetaDataTile(page, self.request)
        result = tile()
        self.assertTrue('Green Bay, WI' in result)
        self.assertTrue('name="location"' in result)
