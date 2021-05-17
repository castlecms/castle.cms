import unittest

from castle.cms.constants import AUDIT_CACHE_DIRECTORY
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from diskcache import Cache
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles


class TestAudit(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_cache_object(self):
        obj = api.content.create(type='Document', id='doc1',
                                 container=self.portal)
        api.portal.set_registry_record(
            'collective.elasticsearch.interfaces.IElasticSettings.enabled', True)
        api.content.transition(obj=obj, to_state='published')
        obj.reindexObject()
        obj_id = getattr(obj, '_plone.uuid')
        cache = Cache(AUDIT_CACHE_DIRECTORY)
        self.assertTrue(obj_id in cache)
        cache.clear()
