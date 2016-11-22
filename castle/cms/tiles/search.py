from castle.cms.tiles.base import BaseTile
from plone.autoform import directives as form
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import Interface


class SearchTile(BaseTile):

    @property
    def portal_types(self):
        return self.data.get('portal_types') or []


class ISearchTileSchema(Interface):
    form.widget('portal_types', CheckBoxFieldWidget)
    portal_types = schema.List(
        title=u'Types to search',
        description=u'Leave empty to allow searching all types',
        required=False,
        default=[],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary="castle.cms.vocabularies.ReallyUserFriendlyTypes"))

    placeholder = schema.TextLine(
        title=u'Search input placeholder field',
        default=u'Search...',
        required=True
    )

    search_btn_text = schema.TextLine(
        title=u'Search button text',
        default=u'Search',
        required=True
    )
