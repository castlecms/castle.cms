from zope import schema
from zope.interface import Interface
from plone.autoform import directives as form
from castle.cms.tiles.base import BaseTile
from castle.cms.widgets import RelatedItemFieldWidget
from plone.app.uuid.utils import uuidToCatalogBrain


class StickyFooterTile(BaseTile):

    @property
    def internal_link_url(self):
        internal_link = self.get_data('internal_link')
        if internal_link:
            try:
                brain = uuidToCatalogBrain(internal_link[0])
                if brain:
                    return brain.getURL()
            except Exception:
                pass

    @property
    def link_url(self):
        return self.internal_link_url or self.get_data('external_link')

    def get_data(self, key):
        return (self.data or {}).get(key, None)


class IStickyFooterTileSchema(Interface):

    email_text = schema.TextLine(
        title=u"Footer Title",
        description=u"(appears next to email icon)",
        required=False,
        default=u"",
    )

    description = schema.TextLine(
        title=u"Footer Description",
        description=u"(appears left of button)",
        required=False,
        default=u"",
    )

    button_text = schema.TextLine(
        title=u"Footer button text",
        required=False,
        default=u"Subscribe",
    )

    form.widget(internal_link=RelatedItemFieldWidget)
    internal_link = schema.List(
        title=u"Internal Link",
        description=u"Content that the sticky footer button links to",
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary="plone.app.vocabularies.Catalog"
        ),
    )

    external_link = schema.TextLine(
        title=u"External URL",
        description=u"If no Interal Link selected, the footer button will link to this URL",
        required=False,
        default=u"",
    )
