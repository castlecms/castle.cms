# -*- coding: utf-8 -*-
from castle.cms.behaviors.order import AvailableOrderSource
from castle.cms.behaviors.order import FolderOrder
from castle.cms.ordering.reversed import ReversedOrdering
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME

import unittest


class TestOrdering(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_available_order_vocab(self):
        folder = api.content.create(type='Folder', title='Foobar', container=self.portal)
        self.assertEquals(len(AvailableOrderSource()(folder)), 3)

    def test_getting_value(self):
        folder = api.content.create(type='Folder', title='Foobar', container=self.portal)
        self.assertEquals(folder.folder_order, '')

    def test_setting_value(self):
        folder = api.content.create(type='Folder', title='Foobar', container=self.portal)
        order = FolderOrder(folder)
        order.folder_order = 'reversed'
        self.assertEquals(type(folder.getOrdering()), ReversedOrdering)


class TestReversedOrdering(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_adding_content_adds_to_beginning(self):
        folder = api.content.create(type='Folder', title='Foobar', container=self.portal)
        order = FolderOrder(folder)
        order.folder_order = 'reversed'
        api.content.create(type='Document', id='one', container=folder)
        api.content.create(type='Document', id='two', container=folder)
        self.assertEquals(folder.objectIds(), ['two', 'one'])

    def test_move_objects(self):
        folder = api.content.create(type='Folder', title='Foobar', container=self.portal)
        order = FolderOrder(folder)
        order.folder_order = 'reversed'
        api.content.create(type='Document', id='one', container=folder)
        api.content.create(type='Document', id='two', container=folder)
        api.content.create(type='Document', id='three', container=folder)

        # order should be 3,2,1 right now
        self.assertEquals(folder.objectIds(), ['three', 'two', 'one'])

        # move 3 to end
        folder.moveObjectsByDelta(('three',), 2)

        self.assertEquals(folder.objectIds(), ['two', 'one', 'three'])

    def test_move_to_bottom(self):
        folder = api.content.create(type='Folder', title='Foobar', container=self.portal)
        order = FolderOrder(folder)
        order.folder_order = 'reversed'
        api.content.create(type='Document', id='one', container=folder)
        api.content.create(type='Document', id='two', container=folder)
        api.content.create(type='Document', id='three', container=folder)

        folder.moveObjectsToBottom(('three',))
        self.assertEquals(folder.objectIds(), ['two', 'one', 'three'])

    def test_move_to_top(self):
        folder = api.content.create(type='Folder', title='Foobar', container=self.portal)
        order = FolderOrder(folder)
        order.folder_order = 'reversed'
        api.content.create(type='Document', id='one', container=folder)
        api.content.create(type='Document', id='two', container=folder)
        api.content.create(type='Document', id='three', container=folder)

        folder.moveObjectsToTop(('one',))
        self.assertEquals(folder.objectIds(), ['one', 'three', 'two'])
