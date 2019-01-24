# -*- coding: utf-8 -*-
from castle.cms.tests.utils import render_tile
import json
import unittest

from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.tiles.dynamic import CACHE_KEY
from castle.cms.tiles.dynamic import FIELD_TYPE_MAPPING
from castle.cms.tiles.dynamic import get_tile_manager
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.theming.interfaces import IThemeSettings
from plone.app.theming.utils import applyTheme
from plone.app.theming.utils import createThemeFromTemplate
from plone.app.theming.utils import getTheme
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory
from zope.component import getUtility


class TestDynamicTiles(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

        # part of setup is to always copy the theme to new one
        createThemeFromTemplate('foobar', '', 'castle.theme')
        themeData = getTheme('foobar')
        applyTheme(themeData)
        registry = getUtility(IRegistry)
        theme_settings = registry.forInterface(IThemeSettings, False)
        theme_settings.enabled = True

        directory = queryResourceDirectory('theme', 'foobar')
        directory.makeDirectory('tiles')
        self.tiles_directory = directory['tiles']

        # clear cache
        for key in list(self.request.environ.keys())[:]:
            if key.startswith(CACHE_KEY):
                del self.request.environ[key]

    def _make_tile(self, config, tile_id='foobartile', template='<div>Hello World!</div>'):
        self.tiles_directory.makeDirectory('foobartile')
        tile_dir = self.tiles_directory['foobartile']
        tile_dir.writeFile('config.json', json.dumps(config))
        tile_dir.writeFile('template.html', template)

    def test_provide_tile_in_theme(self):
        self._make_tile({
            "title": "Foobar",
            "category": "media",
            "weight": 200,
            "fields": [{
                "name": "foobar",
                "title": "Text",
                "required": False
            }]
        })

        mng = get_tile_manager(self.request)
        self.assertEqual(len(mng.get_tiles()), 1)

        tile = mng.get_tile('foobartile')
        self.assertIsNotNone(tile)

        self.assertEqual(len(mng.get_tile_fields('foobartile')), 1)

        iface = mng.get_schema('foobartile')
        self.assertEqual(iface.names(), ['foobar'])

    def test_all_fields(self):
        fields = []
        for idx, type_id in enumerate(FIELD_TYPE_MAPPING.keys()):
            fields.append({
                "name": "foobar{}".format(idx),
                "title": "Foobar {}".format(idx),
                "required": False,
                "type": type_id
            })

        self._make_tile({
            "title": "Foobar",
            "category": "media",
            "weight": 200,
            "fields": fields
        })
        mng = get_tile_manager(self.request)

        self.assertEqual(
            len(mng.get_tile_fields('foobartile')),
            len(FIELD_TYPE_MAPPING))

        iface = mng.get_schema('foobartile')
        self.assertEqual(len(iface.names()), len(FIELD_TYPE_MAPPING))

    def test_render_tile(self):
        self._make_tile({
            "title": "Foobar",
            "category": "media",
            "fields": [{
                "name": "foobar",
                "title": "Text",
                "required": False
            }]
        }, template='<div>Hello ${data/foobar}</div>')
        data = {
            'tile_id': 'foobartile',
            'foobar': 'Foobar!'
        }

        result = render_tile(self.request, self.portal,
                             'castle.cms.dynamic', data)
        self.assertIn('Hello Foobar!', result)
