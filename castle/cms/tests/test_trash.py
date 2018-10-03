# -*- coding: utf-8 -*-
import unittest

from castle.cms import trash
from castle.cms.interfaces import ITrashed
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles


class TestTrash(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_trash_object(self):
        doc = api.content.create(type='Document', id='doc1',
                                 container=self.portal)
        trash.object(doc)
        self.assertTrue(ITrashed.providedBy(doc))

    def test_restore_object(self):
        doc = api.content.create(type='Document', id='doc1',
                                 container=self.portal)
        trash.object(doc)
        self.assertTrue(ITrashed.providedBy(doc))
        trash.restore(doc)
        self.assertFalse(ITrashed.providedBy(doc))
