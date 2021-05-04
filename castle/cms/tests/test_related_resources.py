# -*- coding: utf-8 -*-
import unittest

from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from z3c.relationfield import RelationValue
from castle.cms.browser.viewlets.relateditems import ContentRelatedItems


class TestRelatedResources(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.intid_utility = getUtility(IIntIds)

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        self.source_document = self.create_document('source')

    def create_document(self, id):
        return api.content.create(
            type='Document',
            id=id,
            container=self.portal,
        )

    def publish(self, item):
        api.content.transition(
            obj=item,
            to_state='published',
        )
        
    @property
    def related_items(self):
        content_related_items = ContentRelatedItems(
            context=self.source_document,
            request=self.source_document.REQUEST,
            view=self.source_document.view,
        )
        return [
            brain.getObject()
            for brain in content_related_items.related_items()
        ]

    def set_up_target_documents(self):
        target_documents = [
            self.create_document('target_1'),
            self.create_document('target_2'),
        ]
        self.source_document.relatedItems = [
            RelationValue(self.intid_utility.getId(target))
            for target in target_documents
        ]
        self.assertEqual(
            len(self.source_document.relatedItems),
            2,
        )
        return target_documents

    def assertContentRelatedItemsLength(self, asserted_length):
        self.assertEqual(
            len(self.related_items),
            asserted_length,
        )

    def test_display_unpublished_related_items_false_by_default(self):
        display_unpublished_related_items = api.portal.get_registry_record(
            'plone.display_unpublished_related_items',
            default=True,
        )
        self.assertFalse(display_unpublished_related_items)

    def test_content_related_items_override_when_display_unpublished_false(self):
        target_documents = self.set_up_target_documents()
        api.portal.set_registry_record(
            'plone.display_unpublished_related_items',
            False,
        )
        self.assertEqual(len(self.related_items), 0)
        for expected_related_items_count, target_document in enumerate(target_documents, start=1):
            self.assertFalse(target_document in self.related_items)
            self.publish(target_document)
            self.assertEqual(
                len(self.related_items),
                expected_related_items_count,
            )
            self.assertTrue(target_document in self.related_items)

    def test_content_related_items_override_when_display_unpublished_true(self):
        target_documents = self.set_up_target_documents()
        api.portal.set_registry_record(
            'plone.display_unpublished_related_items',
            True,
        )
        self.assertEqual(len(self.related_items), 2)
        for target_document in target_documents:
            self.assertTrue(target_document in self.related_items)
