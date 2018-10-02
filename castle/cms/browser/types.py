# -*- coding: utf-8 -*-
from plone.app.dexterity import _
from plone.app.dexterity.browser import types
from plone.z3cform import layout
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile


class TypeEditForm(types.TypeEditForm):

    # Remove clone button
    def __init__(self, context, request):
        super(TypeEditForm, self).__init__(context, request)
        if 'castlecms-advanced=1' not in request['HTTP_COOKIE']:
            self.buttons = self.buttons.copy().omit('clone')


class TypesListing(types.TypesListing):
    template = ViewPageTemplateFile('templates/types-listing.pt')
    editform_factory = TypeEditForm


# Create a form wrapper so the form gets layout.
TypesListingPage = layout.wrap_form(
    TypesListing, __wrapper_class=types.TypesEditFormWrapper,
    label=_(u'Dexterity Content Types'))
