import json
import logging
import time
import unittest

from plone import api
from plone.app.testing import (TEST_USER_ID, TEST_USER_NAME, login, setRoles)
from Products.CMFCore.utils import getToolByName
import transaction
from zope.annotation.interfaces import IAnnotations

from castle.cms.browser.search import SearchAjax
from castle.cms.indexing import hps
from castle.cms.social import COUNT_ANNOTATION_KEY
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.tests.utils import get_tile


logger = logging.getLogger(__name__)


class TestHPS(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

        if not self._is_enabled():
            return

        transaction.begin()
        folder = api.content.create(
            type='Folder',
            id='folder1',
            container=self.portal,
            title='Foobar folder')
        folder2 = api.content.create(
            type='Folder',
            id='folder2',
            container=folder,
            title='Foobar subfolder')
        doc1 = api.content.create(
            type='Document',
            id='doc1',
            container=folder,
            title='Foobar one')
        doc2 = api.content.create(
            type='Document',
            id='doc2',
            container=folder,
            subject=('foobar',),
            title='Foobar two')
        doc3 = api.content.create(
            type='Document',
            id='doc3',
            container=folder,
            title='Foobar three')
        doc4 = api.content.create(  # noqa: F841
            type='Document',
            id='doc4',
            container=folder,
            title='Foobar four')
        doc5 = api.content.create(
            type='Document',
            id='doc5',
            container=folder2,
            title='Foobar five')
        doc6 = api.content.create(  # noqa: F841
            type='Document',
            id='doc6',
            container=folder,
            title='Foobar six',
            exclude_from_search=True)
        ann = IAnnotations(doc2)
        ann[COUNT_ANNOTATION_KEY] = {
            'twitter_matomo': 5,
            'facebook': 5,
        }
        for item in [folder, doc1, doc2, doc3, doc5]:
            api.content.transition(obj=item, to_state='published')
            item.reindexObject()

        self._hps_update()
        transaction.commit()

        hpsconn = hps.get_connection()
        hpsconn.indices.flush(index=hps.get_index_name())

    def _is_enabled(self):
        if not hps.is_enabled() or not hps.health_is_good():
            logger.warn("disabling hps testing because it's not enabled or there is a connection issue")
            return False
        return True

    def _hps_update(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        hpscat = hps.get_catalog()
        hpscat.recreateCatalog()
        catalog.manage_catalogRebuild()

    def tearDown(self):
        if not self._is_enabled():
            return

        transaction.begin()
        api.content.delete(self.portal.folder1)
        transaction.commit()

    def _test_ajax_search_rank_social(self):
        if not self._is_enabled():
            return

        self.request.form.update({
            'SearchableText': 'Foobar',
            'portal_type': 'Document'
        })
        view = SearchAjax(self.portal, self.request)
        result = json.loads(view())
        self.assertEquals(result['count'], 3)
        self.assertEquals(result['results'][0]['path'], '/folder1/doc2')

    def test_ajax_search_pt(self):
        if not self._is_enabled():
            return

        time.sleep(1)
        self.request.form.update({
            'SearchableText': 'Foobar',
            'portal_type': 'Folder'
        })
        view = SearchAjax(self.portal, self.request)
        result = json.loads(view())
        self.assertEquals(result['count'], 1)
        self.assertEquals(result['results'][0]['path'], '/folder1')

    def test_ajax_search_subject(self):
        if not self._is_enabled():
            return

        time.sleep(1)
        self.request.form.update({
            'SearchableText': 'Foobar',
            'Subject': 'foobar'
        })
        view = SearchAjax(self.portal, self.request)
        result = json.loads(view())
        self.assertEquals(result['count'], 1)
        self.assertEquals(result['results'][0]['path'], '/folder1/doc2')

    def test_es_querylisting_unicode_issue(self):
        if not self._is_enabled():
            return

        tile = get_tile(self.request, self.portal, 'castle.cms.querylisting', {})
        # should not cause errors...
        self.request.form.update({
            'Title': 'ma\xf1on'
        })
        self.assertTrue(tile.filter_pattern_config != '{}')
        tile()

    def test_ajax_search_with_private_parents(self):
        if not self._is_enabled():
            return

        self.request.form.update({
            'SearchableText': 'Foobar',
            # 'Subject': 'foobar'
        })
        time.sleep(3)  # wait a little to let the search catch up?
        view_1 = SearchAjax(self.portal, self.request)
        result_1 = json.loads(view_1())
        self.assertEqual(result_1['count'], 4)
        api.portal.set_registry_record('plone.allow_public_in_private_container', True)
        view_2 = SearchAjax(self.portal, self.request)
        result_2 = json.loads(view_2())
        self.assertEqual(result_2['count'], 5)
