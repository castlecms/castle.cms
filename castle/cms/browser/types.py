# -*- coding: utf-8 -*-
from plone.app.dexterity import _
from plone.app.dexterity.browser import types
from plone.z3cform import layout
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile


class TypesListing(types.TypesListing):
    template = ViewPageTemplateFile('templates/types-listing.pt')

# Create a form wrapper so the form gets layout.
TypesListingPage = layout.wrap_form(
    TypesListing, __wrapper_class=types.TypesEditFormWrapper,
    label=_(u'Dexterity Content Types'))
