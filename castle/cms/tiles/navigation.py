from Products.CMFPlone.interfaces import INavigationSchema
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Acquisition import aq_parent
from castle.cms.interfaces import IGlobalTile
from castle.cms.tiles.base import BaseTile
from castle.cms.tiles.views import BaseTileView
from castle.cms.tiles.views import getTileView
from castle.cms.tiles.views import TileViewsSource
from castle.cms.utils import parse_query_from_data
from castle.cms.widgets import NavigationTypeWidget
from castle.cms.widgets import QueryFieldWidget
from castle.cms.widgets import RelatedItemsFieldWidget
from plone.autoform import directives as form
from plone.dexterity.interfaces import IDexterityContainer
from plone.memoize.instance import memoize
from plone.supermodel import model
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import schema
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary


class NavigationTile(BaseTile):
    implements(IGlobalTile)

    def render(self):
        view = getTileView(self.context, self.request, 'navigation',
                           self.data.get('display_type', 'horizontal') or 'horizontal',
                           default='horizontal')
        if view is None:
            view = HorizontalView(self.context, self.request)

        view.tile = self
        return view()

    def get_label(self, brain):
        try:
            nav_label = brain.navigation_label
            if nav_label:
                return nav_label
        except Exception:
            pass
        return brain.Title

    @property
    def query(self):
        parsed = parse_query_from_data(self.data, self.context)
        # XXX we're forcing location queries to be depth of 1
        if 'path' in parsed:
            parsed['path']['depth'] = 1
        return parsed

    def items(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        query = None
        nav_type = self.data.get('nav_type', 'currentlocation') or 'currentlocation'
        if nav_type in ('query', 'secondlevel', 'currentlocation'):
            if nav_type == 'query':
                query = self.query
            elif nav_type == 'secondlevel':
                section = self.get_section()
                if section is not None:
                    query = self.build_nav_query({
                        'path': {
                            'depth': 1,
                            'query': '/'.join(section.getPhysicalPath())
                        }
                    })
            elif nav_type == 'currentlocation':
                context = self.context
                if hasattr(self, 'data_context'):
                    context = self.data_context
                query = self.build_nav_query({
                    'path': {
                        'depth': 1,
                        'query': '/'.join(context.getPhysicalPath())
                    }
                })
            if query is None:
                return []
            limit = self.data.get('limit') or 10
            items = catalog(**query)[:limit + 40]
            return [i for i in items if i.exclude_from_nav is not True][:limit]
        else:
            uids = self.data.get('content') or []
            results = dict([(b.UID, b) for b in catalog(UID=uids)])
            items = []
            for uid in uids:
                if uid in results:
                    items.append(results[uid])
            return items

    def build_nav_query(self, base_query):
        query = {}

        registry = getUtility(IRegistry)
        navigation_settings = registry.forInterface(
            INavigationSchema,
            prefix="plone"
        )
        query = {
            'sort_on': navigation_settings.sort_tabs_on,
            'portal_type': navigation_settings.displayed_types
        }

        if navigation_settings.sort_tabs_reversed:
            query['sort_order'] = 'reverse'

        if navigation_settings.filter_on_workflow:
            query['review_state'] = navigation_settings.workflow_states_to_show

        query.update(base_query)
        return query

    @memoize
    def get_section(self):
        section = None
        context = self.context
        while not IPloneSiteRoot.providedBy(context):
            section = context
            context = aq_parent(context)
        if section is not None and IDexterityContainer.providedBy(section):
            return section

    @memoize
    def get_parent_uids(self):
        uids = []
        context = self.context
        while not IPloneSiteRoot.providedBy(context):
            uids.append(IUUID(context, None))
            context = aq_parent(context)
        return [uid for uid in uids if uid is not None]


class HorizontalView(BaseTileView):
    name = 'horizontal'
    order = 0
    index = ViewPageTemplateFile('templates/navigation/horizontal.pt')
    tile_name = 'navigation'


class VerticalView(BaseTileView):
    name = 'vertical'
    order = 10
    index = ViewPageTemplateFile('templates/navigation/vertical.pt')
    tile_name = 'navigation'


class INavigationTileSchema(model.Schema):

    display_type = schema.Choice(
        title=u"Display Type",
        source=TileViewsSource('navigation'),
        default='horizontal'
    )

    form.widget(content=RelatedItemsFieldWidget)
    content = schema.List(
        title=u"Navigation items",
        description=u"Select items for navigation",
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
                    u"to list by choosing what to match on. "
                    u"The list of results will be dynamically updated.",
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

    form.widget(nav_type=NavigationTypeWidget)
    nav_type = schema.Choice(
        title=u'Use dynamic query to populate this menu',
        description=u'Otherwise, the navigation will be built from site section',
        vocabulary=SimpleVocabulary([
            SimpleVocabulary.createTerm('query', 'query', u'Query'),
            SimpleVocabulary.createTerm('content', 'content', u'Select items'),
            SimpleVocabulary.createTerm('currentlocation', 'currentlocation', u'Build from here'),
            SimpleVocabulary.createTerm('secondlevel', 'secondlevel',
                                        u'Build from second level from site root'),
        ]),
        default=u'currentlocation')

    limit = schema.Int(
        title=u'Limit',
        description=u'Limited number of items',
        required=True,
        default=10
    )
