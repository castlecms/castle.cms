from castle.cms.testing import CASTLE_PLONE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, setRoles
import unittest
from castle.cms.fragments import FragmentsDirectory, ThemeFragmentsDirectory, FileChangedCacheFactory, FileCacheFactory, FragmentView
from castle.cms.fragments.tiles import FragmentTile
from castle.cms.fragments.interfaces import FRAGMENTS_DIRECTORY
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from plone.app.theming.utils import theming_policy

class FragmentsCacheTesting(unittest.TestCase):
    layer = CASTLE_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_fragment_tiles_get(self):
        # Checks whether or not we can get all the fragmentviews objects from the FragmentDirectory.
        context = self.portal
        fragments_directory = FragmentsDirectory()
        names = fragments_directory.list()
        for name in names:
            result = fragments_directory.get(context, self.request, name)
            self.assertTrue(isinstance(result, FragmentView))

        false_name = "foobar.pt"
        with self.assertRaises(KeyError):
            fragments_directory.get(context, self.request, false_name)
            
    def test_FileChangedCacheCache(self):
        # Tests the FragmentsDirectory caches and find out whether or not we get the same response.
        context = self.portal
        fragments_directory = FragmentsDirectory()
        names = fragments_directory.list()
        directory_path = fragments_directory.directory_path
        for name in names:
            template_path = "%s/%s.pt" % (directory_path, name)
            result =  fragments_directory.cache.get(name, template_path)
            self.assertTrue(isinstance(result, ZopePageTemplate))

        false_name = "foobar"
        template_path = "%s/%s.pt" % (directory_path, false_name)
        result = fragments_directory.cache.get(false_name, template_path)
        self.assertTrue(result == None)

    def test_ThemeFragments_FragmentViewReturn(self):
        # Tests on whether or not we get all FragmentView objects from the ThemeFragmentsDirectory
        theme_fragments_directory = ThemeFragmentsDirectory()
        context = self.portal
        names = theme_fragments_directory.list()
        for name in names:
            result = theme_fragments_directory.get(context, self.request, name)
            self.assertTrue(isinstance(result, FragmentView))

        false_name = "foobar.pt"
        with self.assertRaises(KeyError):
            theme_fragments_directory.get(context, self.request, false_name)

    def test_ThemeFragmentsDirectoryCache(self):
        # Tests whether we are getting the same cache results from the ThemeFragmentsDirectory cache
        theme_fragments_directory = ThemeFragmentsDirectory()
        policy = theming_policy()
        theme_directory = theme_fragments_directory.get_directory()
        names = theme_fragments_directory.list()
        for name in names:
            template_path = "%s/%s.pt" % (FRAGMENTS_DIRECTORY, name)
            result = theme_fragments_directory.get_from_cache(
                policy, theme_directory, name, template_path)
            self.assertTrue(isinstance(result, ZopePageTemplate))

        false_name = "foobar"
        template_path = "%s/%s.pt" % (FRAGMENTS_DIRECTORY, false_name)        
        with self.assertRaises(KeyError):
            theme_fragments_directory.get_from_cache(
                policy, theme_directory, false_name, template_path)

    def test_FileCache_cache(self):
    # Tests the FileCacheFactory get functionality and check to see that the cache structure is correct
        filecache = FileCacheFactory()
        fd  = FragmentsDirectory()
        names = fd.list()
        directory_path = fd.directory_path
        for name in names:
            template_path = "%s/%s.pt" % (directory_path, name)
            result = filecache.get(name, template_path)
            self.assertTrue(isinstance(result, ZopePageTemplate))

        # Checking to make sure the cache structure is correct and backwards compatible
        cache = filecache.get_cache_storage()
        
        for filepath in cache:
            self.assertTrue(type(filepath) == str)
            if cache[filepath]['template'] == None:
                self.assertTrue(cache[filepath]['mtime'] == 0)
            else:
                self.assertTrue(isinstance(cache[filepath]['template'], ZopePageTemplate))
                self.assertTrue(type(cache[filepath]['mtime']) == int or type(cache[filepath]['mtime']) == float)
        # Checking to ensure that not found files return a none

        false_name = "foobar"
        false_template_path = "%s/%s.pt" % (directory_path, false_name)
        result = filecache.get(false_name, false_template_path)
        self.assertTrue(result == None)
        cache = filecache.get_cache_storage()
        self.assertTrue(cache[false_template_path]['template'] == None)
        self.assertTrue(cache[false_template_path]['mtime'] == 0)

    def test_FileChangedCache_cache(self):
    # Tests the FileChangedCacheFactory get functionality and check to see that the cache structure is correct
        filechangedcache = FileChangedCacheFactory()
        fd  = FragmentsDirectory()
        names = fd.list()
        directory_path = fd.directory_path
        for name in names:
            template_path = "%s/%s.pt" % (directory_path, name)
            result = filechangedcache.get(name, template_path)
            self.assertTrue(isinstance(result, ZopePageTemplate))
            
        # Checking to make sure the cache structure is correct and backwards compatible
        cache = filechangedcache.get_cache_storage()
        
        for filepath in cache:
            self.assertTrue(type(filepath) == str)
            if cache[filepath]['template'] == None:
                self.assertTrue(cache[filepath]['mtime'] == 9999999999 or cache[filepath]['mtime'] == 0)
            else: 
                self.assertTrue(isinstance(cache[filepath]['template'], ZopePageTemplate))
                self.assertTrue(type(cache[filepath]['mtime']) == float)

        # Checking to ensure that not found files return a none
        false_name = "barfoo"
        false_template_path = "%s/%s.pt" % (directory_path, false_name)
        result = filechangedcache.get(false_name, false_template_path)
        self.assertTrue(result == None)
        cache = filechangedcache.get_cache_storage()
        self.assertTrue(cache[false_template_path]['template'] == None)
        self.assertTrue(cache[false_template_path]['mtime'] == 9999999999)
