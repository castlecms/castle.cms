# -*- coding: utf-8 -*-
import json
import unittest
from copy import deepcopy

from castle.cms.patterns import CastleSettingsAdapter
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.upgrades import upgrade_2_2_0
from castle.cms.utils import get_upload_fields
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, login, setRoles
from plone.registry.field import List
from plone.registry.interfaces import IRegistry
from plone.registry.record import Record
from zope.component import getUtility


class TestFileUploadFields(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_fallback_to_default_settings_until_upgrade_done(self):
        registry = getUtility(IRegistry)
        del registry.records['castle.file_upload_fields']
        record = Record(List(), [u'title', u'description'])
        registry.records['castle.required_file_upload_fields'] = record
        fields = get_upload_fields(registry)
        self.assertTrue(fields[0]['required'])
        self.assertTrue(fields[1]['required'])
        self.assertEquals(len(fields), 4)

    def test_get_settings(self):
        registry = getUtility(IRegistry)
        fields = deepcopy(registry['castle.file_upload_fields'])
        for field in fields:
            field['required'] = unicode(field['required']).lower()
        self.assertEquals(len(get_upload_fields(registry)), 5)
        fields.append({
            u'name': u'foobar',
            u'label': u'Foobar',
            u'widget': u'text',
            u'required': u'false',
            u'for-file-types': u'*'
        })
        registry['castle.file_upload_fields'] = fields
        self.assertEquals(len(get_upload_fields(registry)), 6)

    def test_handle_bad_field_values(self):
        # requires fields defined
        registry = getUtility(IRegistry)
        fields = deepcopy(registry['castle.file_upload_fields'])
        fields.append({})
        registry['castle.file_upload_fields'] = deepcopy(fields)
        self.assertEquals(len(get_upload_fields(registry)), 5)

        # auto fill in for missing
        fields.append({
            u'name': u'foobar'
        })
        registry['castle.file_upload_fields'] = fields

        fields = get_upload_fields(registry)
        self.assertEquals(len(fields), 6)
        self.assertEquals(fields[-1]['label'], 'Foobar')
        self.assertEquals(fields[-1]['required'], False)
        self.assertEquals(fields[-1]['widget'], 'text')
        self.assertEquals(fields[-1]['for-file-types'], '*')

    def test_get_pattern_settings(self):
        patterns = CastleSettingsAdapter(self.portal, self.request, None)
        data = patterns()
        self.assertTrue('data-required-file-upload-fields' in data)
        self.assertEquals(data['data-required-file-upload-fields'], json.dumps([u'title']))
        self.assertEquals(
            len(json.loads(data['data-file-upload-fields'])), 5)

    def test_migrate_settings(self):
        registry = getUtility(IRegistry)
        del registry.records['castle.file_upload_fields']
        record = Record(List(), [u'title'])
        registry.records['castle.required_file_upload_fields'] = record

        self.assertIn('castle.required_file_upload_fields', registry.records._fields)
        self.assertIn('castle.required_file_upload_fields', registry.records._values)

        upgrade_2_2_0(self.portal)
        self.assertEquals(len(registry['castle.file_upload_fields']), 4)

        self.assertTrue(registry['castle.file_upload_fields'] is not None)
        self.assertTrue(registry.get('castle.required_file_upload_fields') is None)

        # check registry cleaned up as well
        self.assertIn('castle.file_upload_fields', registry.records._fields)
        self.assertIn('castle.file_upload_fields', registry.records._values)
        self.assertNotIn('castle.required_file_upload_fields', registry.records._fields)
        self.assertNotIn('castle.required_file_upload_fields', registry.records._values)

        # also, test we can safely run it again without overwritting existing values
        fields = deepcopy(registry['castle.file_upload_fields'])
        fields.append({
            u'name': u'foobar',
            u'label': u'Foobar',
            u'widget': u'text',
            u'required': u'false',
            u'for-file-types': u'*'
        })
        registry['castle.file_upload_fields'] = fields
        upgrade_2_2_0(self.portal)
        self.assertEquals(len(registry['castle.file_upload_fields']), 5)
