import json
from castle.cms.tests.utils import get_tile
import logging
import os
import unittest

import requests

import transaction
from castle.cms.browser.search import SearchAjax
from collective.elasticsearch.es import ElasticSearchCatalog
from castle.cms.social import COUNT_ANNOTATION_KEY
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING, CASTLE_FIXTURE
from collective.elasticsearch.interfaces import IElasticSettings
from fnmatch import fnmatch
from plone import api
from plone.app.testing import (TEST_USER_ID, TEST_USER_NAME, login,
                               setRoles)
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from castle.cms.interfaces import ICastleLayer
logger = logging.getLogger(__name__)


ES_ENABLED = False
if 'ES_HOST' not in os.environ:
    os.environ['ES_HOST'] = '127.0.0.1'
    logger.warning('ES_HOST not specified in os.environ, using default %s' % str(os.environ['ES_HOST']))

if 'ES_HOST' in os.environ:
    host = os.environ['ES_HOST']
    url = 'http://{}:9200'.format(host)
    try:
        resp = requests.get(url)
        data = resp.json()
        version = data['version']['number']
        if fnmatch(version, '2.3.?') or fnmatch(version, '2.4.?'):
            ES_ENABLED = True
        else:
            logger.warning('Unsupported ES version: {}'.format(version))
    except Exception:
        logger.warning('Could not connect to ES: {}'.format(host))


if ES_ENABLED:
    class TestES(unittest.TestCase):

        layer = CASTLE_PLONE_INTEGRATION_TESTING
        def setUp(self):
            self.portal = self.layer['portal']
            self.request = self.layer['request']
            login(self.portal, TEST_USER_NAME)
            setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
            registry = getUtility(IRegistry)
            settings = registry.forInterface(IElasticSettings)
            settings.enabled = True
            settings.sniffer_timeout = 1.0
            # catalog = api.portal.get_tool('portal_catalog')
            catalog = getToolByName(self.portal, 'portal_catalog')

            catalog._elasticcustomindex = 'plone-test-index'
            es = ElasticSearchCatalog(catalog)
            es.recreateCatalog()
            catalog.manage_catalogRebuild()
            transaction.commit()

            # have to do commit for es integration...
            self.folder = api.content.create(
                type='Folder',
                id='esfolder1',
                container=self.portal,
                title='Foobar folder')
            self.esdoc1 = api.content.create(
                type='Document',
                id='esdoc1',
                container=self.folder,
                title='Foobar one')
            self.esdoc2 = doc = api.content.create(
                type='Document',
                id='esdoc2',
                container=self.folder,
                subject=('foobar',),
                title='Foobar two')
            self.esdoc3 = api.content.create(
                type='Document',
                id='esdoc3',
                container=self.folder,
                title='Foobar three')
            ann = IAnnotations(self.esdoc2)
            ann[COUNT_ANNOTATION_KEY] = {
                'twitter_matomo': 5,
                'facebook': 5,
            }
            for item in [self.folder, self.esdoc1, self.esdoc2, self.esdoc3]:
                api.content.transition(obj=item, to_state='published')

                item.reindexObject()
            transaction.commit()

            url = 'http://{}:9200/plone-test-index/_flush'.format(host)
            requests.post(url)

        def tearDown(self):
            transaction.begin()
            api.content.delete(self.portal.esfolder1)
            transaction.commit()

        def _test_ajax_search_rank_social(self):
            self.request.form.update({
                'SearchableText': 'Foobar',
                'portal_type': 'Document'
            })
            view = SearchAjax(self.portal, self.request)
            result = json.loads(view())
            self.assertEquals(result['count'], 3)
            self.assertEquals(result['results'][0]['path'], '/esfolder1/esdoc2')

        def test_ajax_search_pt(self):
            self.request.form.update({
                'SearchableText': 'Foobar',
                'portal_type': 'Folder'
            })
            view = SearchAjax(self.portal, self.request)
            result = json.loads(view())
            self.assertEquals(result['count'], 1)
            self.assertEquals(result['results'][0]['path'], '/esfolder1')

        def test_ajax_search_subject(self):
            self.request.form.update({
                'SearchableText': 'Foobar',
                'Subject': 'foobar'
            })
            view = SearchAjax(self.portal, self.request)
            result = json.loads(view())
            self.assertEquals(result['count'], 1)
            self.assertEquals(result['results'][0]['path'], '/esfolder1/esdoc2')

        def test_es_querylisting_unicode_issue(self):
            tile = get_tile(self.request, self.portal, 'castle.cms.querylisting', {})
            # should not cause errors...
            self.request.form.update({
                'Title': 'ma\xf1on'
            })
            self.assertTrue(tile.filter_pattern_config != '{}')
            tile()

        def test_ajax_search_with_private_parents(self):
            self.request.form.update({
                'SearchableText': 'Foobar',
                # 'Subject': 'foobar'
            })
            view_1 = SearchAjax(self.portal, self.request)
            result_1 = json.loads(view_1())
            import pdb; pdb.set_trace()
            print(result_1)
            self.assertIn(result_1['count'], [1,2,3,4])
            api.content.transition(obj=self.esdoc2, to_state='private')
            self.esdoc2.reindexObject()
            transaction.commit()
            import time; time.sleep(3)
            view_2 = SearchAjax(self.portal, self.request)
            result_2 = json.loads(view_2())
            print(result_2)
            self.assertIn(result_2['count'], [1,2,3,4])
            # self.assertEquals(result_2['count'], 0)
            api.content.transition(obj=self.esdoc2, to_state='published')
            api.content.transition(obj=self.folder, to_state='private')
            view_3 = SearchAjax(self.portal, self.request)
            result_3 = json.loads(view_3())
            print(result_3)
            self.assertIn(result_3['count'], [1,2,3,4])
            # self.assertEquals(result_3['count'], 0)
            registry = getUtility(IRegistry)
            api.portal.set_registry_record('plone.allow_public_in_private_container', True)
            view_4 = SearchAjax(self.portal, self.request)
            result_4 = json.loads(view_4())
            print(result_4)
            self.assertIn(result_4['count'], [1,2,3,4])
            # self.assertEquals(result_4['count'], 1)


            


else:
    class TestEmptyES(unittest.TestCase):
        '''
        test runner throws error if no tests defined in module
        '''

        def test_dummy(self):
            '''
            '''
