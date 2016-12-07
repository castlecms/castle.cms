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


class TestPageLayoutSelector(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_get_front_page(self):
        view = content.PageLayoutSelector(self.portal['front-page'], self.request)
        result = json.loads(view())
        self.assertEqual(result['success'], True)
        self.assertEqual(result['page_layout'], 'frontpage.html')
        self.assertEqual(result['section_layout'], None)

    def test_set_front_page(self):
        view = content.PageLayoutSelector(self.portal['front-page'], self.request)
        self.request.form.update({
            'data': json.dumps({
                'page_layout': 'foobar.html',
                'section_layout': 'foobar.html'
            }),
            'action': 'save'
        })
        view()

        # check results...
        del self.request.form['action']
        result = json.loads(view())
        self.assertEqual(result['success'], True)
        self.assertEqual(result['page_layout'], 'foobar.html')
        self.assertEqual(result['section_layout'], 'foobar.html')

        # also check that the registry entry value set since front page is default
        # page for site
        self.assertEqual(
            self.portal.portal_registry['castle.cms.default_layout'],
            'foobar.html')
