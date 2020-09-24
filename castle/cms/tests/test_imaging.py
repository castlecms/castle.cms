# -*- coding: utf-8 -*-
import unittest

from castle.cms import indexers
from castle.cms.interfaces import IReferenceNamedImage
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.widgets import LeadImageFocalNamedImageFieldWidget
from plone import api
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.namedfile.file import NamedBlobImage
from plone.namedfile.tests.test_image import zptlogo
from plone.uuid.interfaces import IUUID
from z3c.form.interfaces import IDataConverter
from zope.component import getMultiAdapter


b64_image = "data:image/gif;base64,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"  # noqa


class BaseTest(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def _get_image(self):
        return NamedBlobImage(zptlogo, contentType='image/jpeg')

    def _get_widget(self, context=None):
        if context is None:
            context = api.content.create(type='Document', title='foobar',
                                         container=self.portal)
        widget = LeadImageFocalNamedImageFieldWidget(
            ILeadImage['image'],
            self.request
        )
        widget.context = context
        widget.id = 'widget.id.image'
        widget.name = 'widget.name.image'
        widget.value = self._get_image()

        return widget

    def _get_converter(self, widget=None, context=None):
        if widget is None:
            widget = self._get_widget(context=context)
        return getMultiAdapter((ILeadImage['image'], widget), IDataConverter)

    def _get_value(self, context):
        converter = self._get_converter(context=context)
        self.request.form.update({
            converter.widget.name + '.filename': 'image.gif',
            converter.widget.name + '.focalX': '1',
            converter.widget.name + '.focalY': '1'
        })
        return converter.toFieldValue(b64_image)

    def _get_object(self, reference=False):
        context = api.content.create(type='Document', title='foobar2',
                                     container=self.portal)
        api.content.transition(obj=context, to_state='published')
        if reference:
            widget = self._get_widget()
            converter = self._get_converter(widget)
            context.image = converter.toFieldValue('reference:' + IUUID(context))
        else:
            context.image = self._get_value(context)
        return context


class TestImageWidget(BaseTest):

    def test_save_image_focal_point(self):
        widget = self._get_widget()
        converter = self._get_converter(widget)
        self.request.form.update({
            widget.name + '.filename': 'image.gif',
            widget.name + '.focalX': '1',
            widget.name + '.focalY': '1'
        })
        result = converter.toFieldValue(b64_image)
        self.assertTrue(hasattr(result, 'focal_point'))
        self.assertTrue(hasattr(widget.context, '_image_focal_point'))

    def test_save_image(self):
        widget = self._get_widget()
        converter = self._get_converter(widget)
        self.request.form.update({
            widget.name + '.filename': 'image.gif'
        })
        result = converter.toFieldValue(b64_image)
        self.assertEquals(type(result), NamedBlobImage)

    def test_save_image_reference(self):
        context = api.content.create(type='Document', title='foobar2',
                                     container=self.portal)
        api.content.transition(obj=context, to_state='published')
        widget = self._get_widget()
        converter = self._get_converter(widget)
        result = converter.toFieldValue('reference:' + IUUID(context))
        self.assertTrue(IReferenceNamedImage.providedBy(result))


class TestIndexImage(BaseTest):

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_index_focal_point(self):
        context = self._get_object()
        value = indexers.image_info(context)()
        self.assertEquals(value['focal_point'], [1, 1])

    def test_index_reference(self):
        reference = api.content.create(type='Document', title='foobar2',
                                       container=self.portal)
        api.content.transition(obj=reference, to_state='published')
        context = self._get_object(reference)
        indexer = indexers.image_info(context)
        value = indexer()
        self.assertEquals(value['reference'], IUUID(context))
