# -*- coding: utf-8 -*-
from castle.cms.browser.controlpanel.site import SiteControlPanelForm
from castle.cms.interfaces import ICastleLayer
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.validators import _iter_widgets, find_backend_urls, is_content_save_form
from plone import api
from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.textfield.value import RichTextValue
from plone.app.tiles.browser.add import DefaultAddForm as TileAddForm
from plone.dexterity.browser.edit import DefaultEditForm
from z3c.form import interfaces
from z3c.form.interfaces import IValidator
from zope.component import getMultiAdapter
from zope.interface import Invalid
from zope.interface import alsoProvides
from zope.schema import Text
from zope.schema.interfaces import IBool

import unittest


class TestBackendUrlValidator(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        alsoProvides(self.request, ICastleLayer)
        alsoProvides(self.request, interfaces.IFormLayer)
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        self.request.form.clear()
        if hasattr(self.request, '_castle_backend_url_utils'):
            del self.request._castle_backend_url_utils
        api.portal.set_registry_record('plone.public_url', u'http://www.example.com')
        api.portal.set_registry_record(
            'plone.backend_url',
            (u'http://edit.example.com', u'https://cms.example.com/site'),
        )
        self.doc = api.content.create(
            type='Document',
            id='backend-url-doc',
            title=u'Original title',
            container=self.portal,
        )

    def _validator(self, form, field):
        return getMultiAdapter(
            (self.doc, self.request, form, field, None),
            IValidator,
        )

    def _edit_form(self):
        return DefaultEditForm(self.doc, self.request)

    def test_validator_rejects_backend_host(self):
        validator = self._validator(self._edit_form(), Text(__name__='description'))
        with self.assertRaises(Invalid) as error:
            validator.validate(u'See http://edit.example.com/secret')
        self.assertIn(u'edit.example.com', unicode(error.exception))

    def test_validator_rejects_second_backend_url(self):
        validator = self._validator(self._edit_form(), Text(__name__='description'))
        with self.assertRaises(Invalid) as error:
            validator.validate(u'https://cms.example.com/site/page')
        self.assertIn(u'cms.example.com/site', unicode(error.exception))

    def test_validator_allows_public_text(self):
        validator = self._validator(self._edit_form(), Text(__name__='description'))
        validator.validate(u'See http://www.example.com/public')

    def test_validator_allows_backend_host_when_it_is_public(self):
        api.portal.set_registry_record('plone.public_url', u'http://edit.example.com')
        self.request._castle_backend_url_utils = None
        validator = self._validator(self._edit_form(), Text(__name__='description'))
        validator.validate(u'See http://edit.example.com/secret')

    def test_validator_rejects_rich_text(self):
        validator = self._validator(self._edit_form(), Text(__name__='text'))
        value = RichTextValue(
            raw=u'<p>http://edit.example.com/body</p>',
            mimeType=u'text/html',
            outputMimeType=u'text/x-html-safe',
        )
        with self.assertRaises(Invalid):
            validator.validate(value)

    def test_validator_rejects_unchanged_stored_value(self):
        self.doc.description = u'Already has http://edit.example.com/old'
        validator = self._validator(self._edit_form(), IDublinCore['description'])
        with self.assertRaises(Invalid):
            validator.validate(interfaces.NOT_CHANGED)

    def test_validator_ignores_site_control_panel(self):
        form = SiteControlPanelForm(self.portal, self.request)
        self.assertFalse(is_content_save_form(form))
        validator = self._validator(form, Text(__name__='description', required=False))
        validator.validate(u'http://edit.example.com/settings')

    def test_fieldset_group_uses_parent_edit_form(self):
        class Group(object):
            def __init__(self, parent):
                self.parentForm = parent

        self.assertTrue(is_content_save_form(Group(self._edit_form())))
        self.assertTrue(is_content_save_form(TileAddForm(self.doc, self.request)))

    def test_find_backend_urls_walks_nested_values(self):
        from castle.cms.browser.content import BackendUrlUtils
        found = find_backend_urls(
            {'body': [u'plain', u'http://edit.example.com/nested']},
            BackendUrlUtils(),
        )
        self.assertEqual(found, [u'edit.example.com'])

    def test_edit_save_is_rejected(self):
        self.doc.description = u'Keep this summary'
        form = self._edit_form()
        form.update()
        self._submit(form, {
            'title': u'Changed title',
            'description': u'Visit http://edit.example.com/secret',
            'changeNote': u'Test edit',
        })
        form.update()

        self.assertEqual(self.doc.title, u'Original title')
        self.assertEqual(self.doc.description, u'Keep this summary')
        self.assertIn(u'edit.example.com', unicode(form.status))
        self.assertIn(u'cannot be saved', unicode(form.status))

    def test_edit_save_allows_clean_content(self):
        form = self._edit_form()
        form.update()
        self._submit(form, {
            'title': u'Changed title',
            'description': u'A public summary',
            'changeNote': u'Test edit',
        })
        form.update()

        self.assertEqual(self.doc.title, u'Changed title')
        self.assertEqual(self.doc.description, u'A public summary')

    def _submit(self, form, overrides):
        self.request.form.clear()
        for widget in _iter_widgets(form):
            if widget.mode == 'display':
                continue
            field_name = widget.field.__name__
            if field_name in overrides:
                raw = overrides[field_name]
            else:
                raw = self._widget_request_value(widget)
            if raw is None:
                continue
            self.request.form[widget.name] = raw
        save_name = None
        for action in form.actions.values():
            if action.name.endswith('.save'):
                save_name = action.name
                break
        if save_name is None:
            self.fail('Save button was not on the edit form')
        self.request.form[save_name] = u'Save'

    def _widget_request_value(self, widget):
        value = widget.value
        if isinstance(value, bool):
            return u'selected' if value else None
        if isinstance(value, basestring):
            return value or None
        if isinstance(value, (list, tuple)):
            if value:
                return list(value)
            if IBool.providedBy(widget.field):
                # An unchecked required bool is stored as the schema missing
                # value, so the widget has no token to post. Send its true
                # token so the rest of the form can validate.
                return [self._true_token(widget)]
        return None

    def _true_token(self, widget):
        try:
            widget.updateTerms()
            for term in widget.terms:
                if term.value is True:
                    return term.token
        except Exception:
            pass
        return u'selected'
