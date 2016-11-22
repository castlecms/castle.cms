# -*- coding: utf-8 -*-
from castle.cms.files.duplicates import DuplicateDetector
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IUUID

import unittest


class TestDuplicateDetector(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_register(self):
        dd = DuplicateDetector()
        hash_ = 'foobar'
        doc = api.content.create(
            type='Document',
            id='folder',
            container=self.portal)
        dd.register(doc, hash_)

        self.assertEqual(IUUID(dd.get_object(hash_)), IUUID(doc))
