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

DEFAULT_ITEM_COUNT = 10


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
        except:
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
        brains = []
        query = None
        nav_type = self.data.get('nav_type', 'currentlocation') or 'currentlocation'
        depth = self.data.get('depth', 1)
        if nav_type in ('query', 'secondlevel', 'currentlocation'):
            if nav_type == 'query':
                query = self.query
            elif nav_type == 'secondlevel':
                section = self.get_section()
                if section is not None:
                    query = self.build_nav_query({
                        'path': {
                            'depth': depth,
                            'query': '/'.join(section.getPhysicalPath())
                        }
                    })
            elif nav_type == 'currentlocation':
                context = self.context
                if hasattr(self, 'data_context'):
                    context = self.data_context
                query = self.build_nav_query({
                    'path': {
                        'depth': depth,
                        'query': '/'.join(context.getPhysicalPath())
                    }
                })
            if query is None:
                return []
            limit = self.data.get('limit') or DEFAULT_ITEM_COUNT
            items = catalog(**query)[:limit + 40]
            brains = [i for i in items if i.exclude_from_nav is not True][:limit]
        else:
            '''
            This is the "select content" case. Don't need to run any queries,
            so we're doing this separately.
            '''
            uids = self.data.get('content') or []
            results = dict([(b.UID, b) for b in catalog(UID=uids)])
            items = []
            for uid in uids:
                if uid in results:
                    items.append(results[uid])
            brains = items

            if depth > 1:
                paths = [x.getPath() for x in brains]
                new_query = self.build_nav_query({
                    'path': {
                        'depth': depth,
                        'query': paths
                    }
                })

                brains = catalog(**new_query)

        def find_parent(tree, child):
            '''
            This method takes a new content item, and appends it to the content
            tree in the correct location
            '''

            done = False
            current = tree

            while not done:
                # We're basically just walking a directory tree
                # as long as the paths match, keep going deeper until
                # the item we're placing is in the correct place

                found = False
                for item in current['sub_items']:
                    if item['path'] in child[0]:
                        current = item
                        found = True

                        # need to break, or we'll keep looking at the current
                        # level
                        break

                if not found:
                    # there's no objects at this level in the tree
                    # that "child" can fit into, so place it along side
                    done = True

            current['sub_items'].append({
                'path': child[0],
                'obj': child[1],
                'sub_items': []
            })

            return tree

        brain_listing = [[x.getPath(), x] for x in brains]
        sorted_brain_listing = sorted(brain_listing, key=lambda x: x[0])

        limit = self.data.get('limit') or DEFAULT_ITEM_COUNT
        sorted_brain_listing = sorted_brain_listing[:limit]

        tree = {'path': '', 'obj': None, 'sub_items': []}
        for brain in sorted_brain_listing:
            tree = find_parent(tree, brain)

        return tree

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
    inner_template = ViewPageTemplateFile('templates/navigation/horizontal_inner.pt')
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

    depth = schema.Int(
        title=u'Navigation Depth',
        description=u"How many levels of navigation to display",
        required=False,
        default=1
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
        default=DEFAULT_ITEM_COUNT
    )
