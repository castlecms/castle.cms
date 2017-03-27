# -*- coding: utf-8 -*-
from castle.cms.tiles.base import ContentTile  # noqa b/w
from castle.cms.widgets import ImageRelatedItemsFieldWidget
from castle.cms.widgets import QueryFieldWidget
from castle.cms.widgets import RelatedItemFieldWidget
from castle.cms.widgets import UseQueryWidget
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema
from zope.interface import Invalid
from zope.interface import invariant


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


class IImagesTileSchema(model.Schema):

    form.widget(use_query=UseQueryWidget)
    use_query = schema.Bool(
        title=u'Use dynamic query',
        default=False)

    form.widget('images', ImageRelatedItemsFieldWidget)
    images = schema.List(
        title=u"Images",
        description=u"Select images or folders of images to display in "
                    u"gallery",
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        ),
        required=False
    )

    form.widget(query=QueryFieldWidget)
    query = schema.List(
        title=u'Search terms',
        description=u"Define the search terms for the images you want to use. "
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
