from castle.cms.behaviors.location import ILocation
from castle.cms.tiles.base import BaseTile
from castle.cms.utils import parse_query_from_data
from castle.cms.widgets import MapMarkersFieldWidget
from castle.cms.widgets import MapPointFieldWidget
from castle.cms.widgets import QueryFieldWidget
from castle.cms.widgets import RelatedItemsFieldWidget
from castle.cms.widgets import UseQueryWidget
from plone import api
from plone.autoform import directives as form
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from plone.tiles.interfaces import IPersistentTile
from zope import schema
from zope.component import getUtility
from zope.interface import implements
from zope.interface import Invalid
from zope.interface import invariant

import json


ITEM_TEMPLATE = """
<h3><a href="%(url)s">%(title)s</a></h3>
<p>%(description)s</p>
"""


class MapTile(BaseTile):
    implements(IPersistentTile)

    def render(self):
        return self.index()

    @property
    def query(self):
        parsed = parse_query_from_data(self.data, self.context)
        parsed['sort_limit'] = self.data.get('limit', 20) or 20
        return parsed

    def json_data(self):

        registry = getUtility(IRegistry)
        typesUseViewActionInListings = frozenset(
            registry.get('plone.types_use_view_action_in_listings', []))

        try:
            markers = json.loads(self.data.get('custom_markers', '[]') or '[]')
        except Exception:
            markers = []
        brains = []
        catalog = api.portal.get_tool('portal_catalog')
        if self.data.get('use_query') in ('True', True, 'true'):
            brains = catalog(**self.query)[:self.data.get('limit', 20) or 20]
        else:
            brains = catalog(UID=self.data.get('content', []) or [])
        for brain in brains:
            ob = brain.getObject()
            data = ILocation(ob, None)
            if data is None:
                continue
            try:
                coords = json.loads(data.coordinates)
            except Exception:
                continue
            if not coords:
                continue

            if type(coords) == dict:
                coords = [coords]

            title = ob.Title()
            url = ob.absolute_url()
            if ob.portal_type in typesUseViewActionInListings:
                url += '/view'
            html = ITEM_TEMPLATE % {
                'title': title,
                'description': ob.Description(),
                'url': url
            }

            for coord in coords:
                coord = coord.copy()
                coord['popup'] = html
                markers.append(coord)
        data = {
            'initialZoom': self.data.get('initialZoom', 11) or 11,
            'height': self.data.get('height', 200) or 200,
            'center': self.data.get('center'),
            'markers': json.dumps(markers)
        }
        return json.dumps(data)


def validate_center(center):
    try:
        center = json.loads(center)
        if len(center) == 0:
            return False
    except Exception:
        pass
    return True


class IMapTileSchema(model.Schema):

    form.widget(use_query=UseQueryWidget)
    use_query = schema.Bool(
        title=u'Use dynamic query',
        description=u'For map content.',
        default=False)

    form.widget(content=RelatedItemsFieldWidget)
    content = schema.List(
        title=u"Items",
        description=u"Selected items to show on map",
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    form.widget(query=QueryFieldWidget)
    query = schema.List(
        title=u'Search terms',
        description=u"Define the search terms for the items you want "
                    u"dynamically include in this map",
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

    limit = schema.Int(
        title=u'Limit',
        description=u'Limit Search Results',
        required=False,
        default=20,
        min=1,
    )

    form.widget(custom_markers=MapMarkersFieldWidget)
    custom_markers = schema.Text(
        title=u'Custom Markers',
        default=u'[]',
        required=False
    )

    form.widget(center=MapPointFieldWidget)
    center = schema.Text(
        title=u'Center point',
        default=u'{}'
    )

    @invariant
    def validate_center(data):
        try:
            center = json.loads(data.center)
        except Exception:
            return
        if len(center) == 0:
            raise Invalid('Must provide a center point')

    height = schema.Int(
        title=u"Height",
        default=200
    )

    initialZoom = schema.Int(
        title=u"Initial Zoom",
        default=11
    )
