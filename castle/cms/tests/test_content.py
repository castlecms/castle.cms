# -*- coding: utf-8 -*-
import json
import unittest
from copy import deepcopy
from io import BytesIO

from castle.cms.browser import content
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces.syndication import IFeedSettings
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility


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

    def test_publish_content_twice(self):
        doc = api.content.create(
            type='Document',
            id='doc',
            container=self.portal)
        pc = content.PublishContent(doc, self.request)
        pc()
        # second once used to cause InvalidParameterError
        pc()
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

    def test_upload(self):
        self.request.form.update({
            'action': 'chunk-upload',
            'chunk': '1',
            'chunkSize': 1024,
            'totalSize': 1024 * 5,
            'file': BytesIO('X' * 1024),
            'name': 'foobar.bin'
        })
        cc = content.Creator(self.portal, self.request)
        data = json.loads(cc())
        self.assertTrue('id' in data)
        self.assertTrue(data['success'])
        self.request.form.update({
            'id': data['id']
        })

        for idx in range(4):
            self.request.form.update({
                'action': 'chunk-upload',
                'chunk': str(idx + 2),
                'file': BytesIO('X' * 1024)
            })
            cc = content.Creator(self.portal, self.request)
            data = json.loads(cc())
            self.assertTrue(data['success'])

        self.assertTrue(data['valid'])
        self.assertTrue('url' in data)

        fileOb = api.content.get(path='/file-repository/foobar.bin')
        self.assertEquals(fileOb.file.data, 'X' * 1024 * 5)
        return fileOb

    def test_update_upload(self):
        fileOb = self.test_upload()
        self.request.form.update({
            'action': 'chunk-upload',
            'chunk': '1',
            'chunkSize': 1024,
            'totalSize': 1024,
            'file': BytesIO('U' * 1024),
            'name': 'foobar2.bin',
            'content': IUUID(fileOb),
            'field': 'file'
        })
        cc = content.Creator(self.portal, self.request)
        data = json.loads(cc())
        self.assertTrue(data['valid'])
        self.assertTrue('url' in data)
        fileOb = api.content.get(path='/file-repository/foobar.bin')
        self.assertEquals(fileOb.file.data, 'U' * 1024)

    def test_tmp_upload(self):
        fileOb = self.test_upload()
        self.request.form.update({
            'action': 'chunk-upload',
            'chunk': '1',
            'chunkSize': 1024,
            'totalSize': 1024,
            'file': BytesIO('T' * 1024),
            'name': 'foobar2.bin',
            'content': IUUID(fileOb),
            'field': 'tmp_blarg'
        })
        cc = content.Creator(self.portal, self.request)
        data = json.loads(cc())
        self.assertTrue(data['valid'])
        self.assertTrue('url' in data)
        fileOb = api.content.get(path='/file-repository/foobar.bin')

        # should not change!
        self.assertEquals(fileOb.file.data, 'X' * 1024 * 5)

        # tmp file should be uploaded
        annotations = IAnnotations(fileOb)
        tmp_files = annotations['_tmp_files']
        self.assertTrue('tmp_blarg' in tmp_files)

    def test_create_folders(self):
        self.request.form.update({
            'action': 'create',
            'basePath': 'foo/bar',
            'id': 'foobar',
            'title': 'Foobar',
            'selectedType[id]': 'Document',
            'transitionTo': 'publish'
        })
        cc = content.Creator(self.portal, self.request)
        data = json.loads(cc())
        ob = api.content.get(path='/foo/bar/foobar')
        self.assertTrue(ob is not None)
        self.assertEquals(
            data['base_url'], 'http://nohost/plone/foo/bar/foobar')
        self.assertEquals(
            api.content.get_state(ob), 'published')

    def test_save_file_saves_custom_field_values(self):

        # add new field
        registry = getUtility(IRegistry)
        fields = deepcopy(registry['castle.file_upload_fields'])
        for f in fields:
            f['required'] = unicode(f['required']).lower()
        fields.append({
            u'name': u'foobar',
            u'label': u'Foobar',
            u'widget': u'text',
            u'required': u'false',
            u'for-file-types': u'*'
        })
        registry['castle.file_upload_fields'] = fields

        self.request.form.update({
            'action': 'chunk-upload',
            'chunk': '1',
            'chunkSize': 1024,
            'totalSize': 1024,
            'file': BytesIO('X' * 1024),
            'name': 'foobar.bin',
            'title': 'Foobar',
            'foobar': 'Some value here'
        })
        cc = content.Creator(self.portal, self.request)
        cc()

        fileOb = api.content.get(path='/file-repository/foobar.bin')
        self.assertEquals(fileOb.file.data, 'X' * 1024)
        self.assertEquals(fileOb.foobar, 'Some value here')
        return fileOb

    def test_content_should_implement_empty_feed_settings_to_prevent_errors(self):
        doc = api.content.create(
            type='Document',
            id='docblah',
            container=self.portal)
        settings = IFeedSettings(doc)
        # should not cause TypeError
        self.assertEquals(settings.feed_types, ())


class TestContentAccess(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        logout()

    def test_accees_denied(self):
        content.Creator(self.portal, self.request)()
        self.assertEquals(self.request.response.getStatus(), 403)

    def test_modify_content_upload_permission(self):
        api.user.create(
            email='foo@bar.com', username='foobar',
            password='foobar', roles=('Member',))
        setRoles(self.portal, 'foobar', (
            'Member', 'Contributor', 'Reviewer'))
        api.user.create(
            email='foo2@bar.com', username='foobar2',
            password='foobar2', roles=('Member',))
        setRoles(self.portal, 'foobar2', (
            'Member', 'Reviewer'))

        login(self.portal, 'foobar')
        self.request.form.update({
            'action': 'chunk-upload',
            'chunk': '1',
            'chunkSize': 1024,
            'totalSize': 1024,
            'file': BytesIO('X' * 1024),
            'name': 'foobar.bin'
        })
        cc = content.Creator(self.portal, self.request)
        data = json.loads(cc())
        fileOb = api.content.get(path='/file-repository/foobar.bin')
        self.assertEquals(fileOb.file.data, 'X' * 1024)

        # and publish the sucker
        api.content.transition(fileOb, 'publish')

        logout()
        login(self.portal, 'foobar2')

        self.request.form.update({
            'action': 'chunk-upload',
            'file': BytesIO('U' * 1024),
            'name': 'foobar2.bin',
            'content': IUUID(fileOb),
            'field': 'file'
        })
        cc = content.Creator(self.portal, self.request)
        data = json.loads(cc())
        self.assertFalse(data['success'])


class TestPageLayoutSelector(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_get_front_page(self):
        view = content.PageLayoutSelector(
            self.portal['front-page'], self.request)
        result = json.loads(view())
        self.assertEqual(result['success'], True)
        self.assertEqual(result['page_layout'], 'frontpage.html')
        self.assertEqual(result['section_layout'], None)

    def test_set_front_page(self):
        view = content.PageLayoutSelector(
            self.portal['front-page'], self.request)
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

        # also check that the registry entry value set since
        # front page is default page for site
        self.assertEqual(
            self.portal.portal_registry['castle.cms.default_layout'],
            'foobar.html')
