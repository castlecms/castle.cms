from castle.cms.test import (
    CASTLE_PLONE_FUNCTIONAL_TESTING,
    CASTLE_PLONE_INTEGRATION_TESTING,
    )

from plone import api
import plone.app.testing
import unittest
from castle.cms.fragments import FragmentsDirectory
from castle.cms.fragments import ThemeFragmentsDirectory
from castle.cms.fragments import FileChangedCacheFactory
from castle.cms.fragments.tiles import FragmentTile
from castle.cms.fragments import FragmentView

class FragmentsCacheTesting(unittest.TestCase):
    layer = CASTLE_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    

    def check_tiles(self):
        # Checks whether or not we can get and render all the fragmentviews objects.
        context = self.portal
        names = FragmentsDirectory.list()
        for name in names:
            result = FragementsDirectory.get(context, self.request, name)
            self.assertTrue(isinstance(result, FragmentView))
            result.index()

    def check_FileChangedCacheCache(self):
        # Tests the caches and find out whether or not we get the same response.
        context = self.portal

    def check_ThemeFragments_FragmentViewReturn(self):
        # Tests on whether or not we get a FragmentView class
        pass

    def check_ThemeFragmentsDirectoryCache(self):
        # Tests whether we are getting the same cache results from the ThemeFragmentsDirectory cache
        pass
