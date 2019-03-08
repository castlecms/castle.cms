# -*- coding: utf-8 -*-
import unittest

from castle.cms.behaviors.location import ILocation
from castle.cms.behaviors.search import ISearch
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.tiles.metadata import MetaDataTile
from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, setRoles


class TestMetadata(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_gives_location(self):
        page = api.content.create(type='Document', title='Foobar',
                                  container=self.portal)
        ldata = ILocation(page)
        ldata.locations = [u'Green Bay, WI']

        tile = MetaDataTile(page, self.request)
        result = tile()
        self.assertTrue('Green Bay, WI' in result)
        self.assertTrue('name="location"' in result)

    def test_robots_default_config(self):
        page = api.content.create(type='Document', title='Foobar',
                                  container=self.portal)

        tile = MetaDataTile(page, self.request)
        result = tile()
        self.assertTrue('index,follow' in result)

    def test_robots_no_value(self):
        page = api.content.create(type='Document', title='Foobar',
                                  container=self.portal)

        search = ISearch(page)
        search.robot_configuration = [u'follow']

        tile = MetaDataTile(page, self.request)
        result = tile()
        self.assertTrue('follow,noindex' in result)

        search = ISearch(page)
        search.robot_configuration = [u'index']

        tile = MetaDataTile(page, self.request)
        result = tile()
        self.assertTrue('index,nofollow' in result)

    def test_robots_values(self):
        page = api.content.create(type='Document', title='Foobar',
                                  container=self.portal)

        search = ISearch(page)
        search.robot_configuration = [
            u'index', u'follow', u'noimageindex', u'noarchive', u'nosnippet']

        tile = MetaDataTile(page, self.request)
        result = tile()
        self.assertTrue('index,follow,noimageindex,noarchive,nosnippet' in result)
