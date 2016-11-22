# -*- coding: utf-8 -*-
from castle.cms.tiles.base import BaseTile
from castle.cms.utils import parse_query_from_data
from castle.cms.widgets import QueryFieldWidget
from castle.cms.widgets import RelatedItemFieldWidget
from castle.cms.widgets import UseQueryWidget
from plone.autoform import directives as form
from plone.supermodel import model
from plone.tiles.interfaces import IPersistentTile
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.interface import implements
from zope.interface import Invalid
from zope.interface import invariant


class ContentTile(BaseTile):
    implements(IPersistentTile)
    default_display_fields = ('title', 'image', 'description')

    def render(self):
        return self.index()

    @property
    def content(self):
        if self.data.get('use_query') in ('True', True, 'true'):
            catalog = getToolByName(self.context, 'portal_catalog')
            items = catalog(**self.query)
            if len(items) > 0:
                return items[0].getObject()
        else:
            return self.utils.get_object(self.data['content'][0])

    @property
    def query(self):
        parsed = parse_query_from_data(self.data, self.context)
        parsed['sort_limit'] = 1
        return parsed

    @property
    def display_fields(self):
        df = self.data.get('display_fields', None)
        if df is None:
            df = self.default_display_fields
        return df


class IContentTileSchema(model.Schema):

    form.widget(use_query=UseQueryWidget)
    use_query = schema.Bool(
        title=u'Use dynamic query',
        default=False)

    form.widget(content=RelatedItemFieldWidget)
    content = schema.List(
        title=u"Item",
        description=u"Selected item to display",
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    @invariant
    def validate_content(data):
        if data.content and len(data.content) != 1:
            raise Invalid("Must select 1 item")

    form.widget(query=QueryFieldWidget)
    query = schema.List(
        title=u'Search terms',
        description=u"Define the search terms for the item you want "
                    u"to list by choosing what to match on. "
                    u"The list of results will be dynamically updated",
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False
    )

    sort_on = schema.TextLine(
        title=u'Sort on',
        description=u"Sort on this index",
        required=False,
    )

    sort_reversed = schema.Bool(
        title=u'Reversed order',
        description=u'Sort the results in reversed order',
        required=False,
    )

    more_text = schema.TextLine(
        title=u'More text',
        default=u'',
        required=False)
