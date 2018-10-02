# -*- coding: utf-8 -*-
from zope.annotation.interfaces import IAnnotations
from castle.cms import utils
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX as TILE_ANNOTATIONS_KEY_PREFIX  # noqa

import unittest
import json
from castle.cms.browser import tiles as tile_views


class TestSlots(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING
    slot_id = 'meta-left-slot'

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        self._create_slot()

    def test_foobar(self):
        pass

    def _create_slot(self):
        annotations = IAnnotations(self.portal)
        tiles = PersistentList()
        for _ in range(2):
            tile_id = utils.get_random_string(30)
            annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id] = PersistentDict({  # noqa
                'foo': 'bar'
            })
            tiles.append({
                'id': tile_id
            })
        annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + self.slot_id] = PersistentDict({  # noqa
            'tiles': tiles
        })

    def ztest_copy_slot(self):
        view = tile_views.MetaTileManager(self.portal, self.request)
        self.request.form.update({
            'metaId': self.slot_id
        })
        new_id = json.loads(view.copy_meta())['newId']
        annotations = IAnnotations(self.portal)
        self.assertTrue(
            TILE_ANNOTATIONS_KEY_PREFIX + '.' + new_id in annotations)
        data = annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + self.slot_id]
        self.assertEquals(data['locked']['user'], TEST_USER_ID)

    def ztest_copy_tiles(self):
        view = tile_views.MetaTileManager(self.portal, self.request)
        self.request.form.update({
            'metaId': self.slot_id
        })
        annotations = IAnnotations(self.portal)
        self.assertEqual(
            len([k for k in annotations.keys()
                 if k.startswith(TILE_ANNOTATIONS_KEY_PREFIX)]),
            3
        )
        view.copy_meta()
        self.assertEqual(
            len([k for k in annotations.keys()
                 if k.startswith(TILE_ANNOTATIONS_KEY_PREFIX)]),
            6
        )

    def ztest_save_slot(self):
        view = tile_views.MetaTileManager(self.portal, self.request)
        self.request.form.update({
            'metaId': self.slot_id
        })
        annotations = IAnnotations(self.portal)
        view.copy_meta()
        self.assertEqual(
            len([k for k in annotations.keys()
                 if k.startswith(TILE_ANNOTATIONS_KEY_PREFIX)]),
            6
        )
        view.save_copy()
        self.assertEqual(
            len([k for k in annotations.keys()
                 if k.startswith(TILE_ANNOTATIONS_KEY_PREFIX)]),
            3
        )

    def ztest_data_is_updated(self):
        view = tile_views.MetaTileManager(self.portal, self.request)
        self.request.form.update({
            'metaId': self.slot_id
        })
        annotations = IAnnotations(self.portal)
        view.copy_meta()
        version_key = view.get_working_copy_key()
        copy_slot = annotations[
            TILE_ANNOTATIONS_KEY_PREFIX + '.' + self.slot_id + '-' + version_key]  # noqa
        tile = copy_slot['tiles'][0]
        tile_id = tile['id']
        tile_data = annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id]
        tile_data['foo'] = 'bozo'
        view.save_copy()
        tile_data = annotations[
            TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id.replace('-' + version_key, '')]  # noqa

        self.assertEquals(tile_data['foo'], 'bozo')

    def ztest_tile_is_deleted(self):
        view = tile_views.MetaTileManager(self.portal, self.request)
        self.request.form.update({
            'metaId': self.slot_id
        })
        annotations = IAnnotations(self.portal)
        view.copy_meta()
        version_key = view.get_working_copy_key()
        copy_slot = annotations[
            TILE_ANNOTATIONS_KEY_PREFIX + '.' + self.slot_id + '-' + version_key]  # noqa
        tile = copy_slot['tiles'][0]
        copy_slot['tiles'].remove(tile)
        tile_id = tile['id']
        del annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id]
        view.save_copy()

        self.assertEqual(
            len([k for k in annotations.keys()
                 if k.startswith(TILE_ANNOTATIONS_KEY_PREFIX)]),
            2
        )

    def ztest_cancel_slot_edit(self):
        view = tile_views.MetaTileManager(self.portal, self.request)
        self.request.form.update({
            'metaId': self.slot_id
        })
        annotations = IAnnotations(self.portal)
        view.copy_meta()
        view.cancel_copy()

        self.assertEqual(
            len([k for k in annotations.keys()
                 if k.startswith(TILE_ANNOTATIONS_KEY_PREFIX)]),
            3
        )
