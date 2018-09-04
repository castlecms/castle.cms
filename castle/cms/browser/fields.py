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
    advancedbtns = EnhancedSchemaListing.buttons.copy()
    regularbtns = EnhancedSchemaListing.buttons.copy().omit('modeleditor')

class TypeFieldsPage(fields.TypeFieldsPage):
    def __init__(self, context, request):
        super(TypeFieldsPage, self).__init__(context, request)
        if pkg_resources.get_distribution('plone.resourceeditor'):
            if 'castlecms-advanced=1' in request['HTTP_COOKIE']:
                EnhancedSchemaListing.buttons = advancedbtns
            else:
                EnhancedSchemaListing.buttons = regularbtns
