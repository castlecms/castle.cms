# -*- coding: utf-8 -*-
import pkg_resources

from plone.app.dexterity.browser import fields
from plone.schemaeditor.browser.schema.listing import ReadOnlySchemaListing
from zope.event import notify
from z3c.form.events import DataExtractedEvent


class EnhancedSchemaListing(fields.EnhancedSchemaListing):
    def extractData(self, setErrors=True):
        data, errors = super(EnhancedSchemaListing, self).extractData(setErrors=setErrors)
        for group in self.groups:
            groupData, groupErrors = group.extractData(setErrors=setErrors)
            data.update(groupData)
            if groupErrors:
                if errors:
                    errors += groupErrors
                else:
                    errors = groupErrors
        for fname, value in data.items():
            if fname not in self.context.schema:
                del data[fname]
        notify(DataExtractedEvent(data, errors, self))
        return data, errors


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

    @property
    def form(self):
        if self.context.fti.hasDynamicSchema:
            return EnhancedSchemaListing
        else:
            return ReadOnlySchemaListing
