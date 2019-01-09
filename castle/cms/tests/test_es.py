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
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from collective.elasticsearch.interfaces import IElasticSettings
from plone import api
from plone.app.testing import (TEST_USER_ID, TEST_USER_NAME, login,
                               setRoles)
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility

logger = logging.getLogger(__name__)


ES_ENABLED = False

if 'ES_HOST' in os.environ:
    host = os.environ['ES_HOST']
    url = 'http://{}:9200'.format(host)
    try:
        resp = requests.get(url)
        data = resp.json()
        version = data['version']['number']
        if version in ('2.3.2', '2.3.3', '2.3.5'):
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
            settings.sniffer_timeout = None
            catalog = getToolByName(self.portal, 'portal_catalog')
            catalog._elasticcustomindex = 'plone-test-index'
            es = ElasticSearchCatalog(catalog)
            es.recreateCatalog()
            catalog.manage_catalogRebuild()
            transaction.commit()

            # have to do commit for es integration...
            folder = api.content.create(
                type='Folder',
                id='esfolder1',
                container=self.portal,
                title='Foobar folder')
            api.content.create(
                type='Document',
                id='esdoc1',
                container=folder,
                title='Foobar one')
            doc = api.content.create(
                type='Document',
                id='esdoc2',
                container=folder,
                subject=('foobar',),
                title='Foobar two')
            api.content.create(
                type='Document',
                id='esdoc3',
                container=folder,
                title='Foobar three')

            ann = IAnnotations(doc)
            ann[COUNT_ANNOTATION_KEY] = {
                'twitter_matomo': 5,
                'facebook': 5,
            }
            doc.reindexObject()
            transaction.commit()

            url = 'http://{}:9200/plone-test-index/_flush'.format(host)
            requests.post(url)

        def tearDown(self):
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

else:
    class TestEmptyES(unittest.TestCase):
        '''
        test runner throws error if no tests defined in module
        '''

        def test_dummy(self):
            '''
            '''
