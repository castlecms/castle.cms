# -*- coding: utf-8 -*-
from castle.cms.browser import content
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IUUID

import json
import unittest


class TestContent(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_dump_data(self):
        doc = api.content.create(
            type='Document',
            id='doc',
            container=self.portal)
        data = content.dump_object_data(doc)
        self.assertEqual(json.loads(data)['uid'], IUUID(doc))

    def test_dump_data_with_view(self):
        folder = api.content.create(
            type='Folder',
            id='file-repository',
            container=self.portal)
        doc = api.content.create(
            type='File',
            id='fi',
            container=folder)
        data = content.dump_object_data(doc)
        self.assertEqual(json.loads(data)['url'], doc.absolute_url() + '/view')

    def test_workflow_transition(self):
        doc = api.content.create(
            type='Document',
            id='doc',
            container=self.portal)
        self.request.form.update({
            'transition_id': 'publish',
            'action': 'transition'
        })
        wf = content.Workflow(doc, self.request)
        wf()
        self.assertEqual(api.content.get_state(doc), 'published')

    def test_check(self):
        self.request.form.update({
            'action': 'check',
            'selectedType[typeId]': 'Folder',
            'basePath': '/',
            'id': 'foobar'
        })
        cc = content.Creator(self.portal, self.request)
        data = cc()
        self.assertEqual(json.loads(data)['valid'], True)
