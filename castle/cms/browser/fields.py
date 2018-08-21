# -*- coding: utf-8 -*-
#from plone.app.dexterity import _
from plone.app.dexterity.browser import fields
from plone.app.dexterity.browser.fields import EnhancedSchemaListing
from plone.app.dexterity.browser.layout import TypeFormLayout
from plone.schemaeditor.browser.schema.listing import ReadOnlySchemaListing
from plone.schemaeditor.browser.schema.listing import SchemaListing
from z3c.form import button

import pkg_resources


if pkg_resources.get_distribution('plone.resourceeditor'):
    but = button.Button('modeleditor', title=u'Edit XML Field Model (if you dare)')
    EnhancedSchemaListing.buttons += button.Buttons(but)
    handler = button.Handler(but, EnhancedSchemaListing.handleModelEdit)
    EnhancedSchemaListing.handlers.addHandler(but, handler)


class TypeFieldsPage(fields.TypeFieldsPage):
    pass
