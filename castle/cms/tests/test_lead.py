# -*- coding: utf-8 -*-
from zope.annotation.interfaces import IAnnotations
from plone.namedfile.file import NamedBlobImage
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IUUID
from castle.cms.interfaces import IReferenceNamedImage
from castle.cms import lead
from plone.app.textfield.value import RichTextValue
from plone.namedfile.tests.test_image import zptlogo
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX

import unittest


class TestLeadImages(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        self.folder_obj = api.content.create(
            type='Folder', container=self.portal, id='testfolder',)
        self.page_obj = api.content.create(
            type='Document', container=self.folder_obj, id='testpage',)
        self.image_obj = api.content.create(
            type='Image', container=self.folder_obj, id='testimage',
            image=NamedBlobImage(zptlogo, contentType='image/jpeg'))
        self.img_uid = IUUID(self.image_obj)

    def test_find_lead_image_in_text(self):
        self.page_obj.text = RichTextValue('''
<p>
<img src="resolveuid/{}/@@images/image/large" />
</p>
        '''.format(
            IUUID(self.image_obj)), mimeType='text/html',
            outputMimeType='text/html')
        image = lead.find_image(self.page_obj)
        self.assertEquals(IUUID(image), self.img_uid)

    def test_find_image_in_html(self):
        image = lead.find_image_in_html('''
<p>
<img src="resolveuid/{}/@@images/image/large" />
</p>
        '''.format(self.img_uid))
        self.assertEquals(IUUID(image), self.img_uid)

    def test_find_image_in_annotation(self):
        image = lead.find_image_in_annotation({
            'image': self.img_uid
        })
        self.assertEquals(IUUID(image), IUUID(self.image_obj))

    def test_find_image_in_annotation_on_object(self):
        annotations = IAnnotations(self.page_obj)
        annotations[ANNOTATIONS_KEY_PREFIX + 'foobar'] = {
            'image': self.img_uid
        }
        image = lead.find_image(self.page_obj)
        self.assertEquals(IUUID(image), self.img_uid)

    def test_find_image_in_annotation_with_html_on_object(self):
        annotations = IAnnotations(self.page_obj)
        annotations[ANNOTATIONS_KEY_PREFIX + 'foobar'] = {
            'content': '''
<p>
<img src="resolveuid/{}/@@images/image/large" />
</p>
            '''.format(self.img_uid)
        }
        image = lead.find_image(self.page_obj)
        self.assertEquals(IUUID(image), self.img_uid)

    def test_add_reference_image(self):
        self.page_obj.text = RichTextValue('''
<p>
<img src="resolveuid/{}/@@images/image/large" />
</p>
        '''.format(self.img_uid),
            mimeType='text/html', outputMimeType='text/html')
        lead.check_lead_image(self.page_obj)
        self.assertTrue(IReferenceNamedImage.providedBy(self.page_obj.image))
        self.assertEquals(self.page_obj.image.reference, self.img_uid)
