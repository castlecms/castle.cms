import json
from urllib import urlencode
from urlparse import parse_qsl

from castle.cms import defaults
from castle.cms.tiles.base import BaseTile
from castle.cms.tiles.base import DisplayTypeTileMixin
from castle.cms.tiles.views import BaseTileView
from castle.cms.tiles.views import TileViewsSource
from castle.cms.utils import parse_query_from_data
from castle.cms.widgets import PreviewSelectFieldWidget
from castle.cms.widgets import QueryFieldWidget
from DateTime import DateTime
from plone.app.z3cform.widget import AjaxSelectFieldWidget
from plone.autoform import directives as form
from plone.memoize.instance import memoize
from plone.supermodel import model
from plone.tiles.interfaces import IPersistentTile
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from unidecode import unidecode
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.interface import implements
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.component import getMultiAdapter
from lxml.html import fromstring
from lxml.html import tostring
from plone import api
from Products.CMFPlone.browser.syndication.adapters import SearchFeed
from Products.CMFPlone.interfaces.syndication import IFeedItem
from zope.component import queryMultiAdapter


SORT_OPTIONS = {
    'effective:reverse': {
        'sort_on': 'effective',
        'sort_order': 'reverse',
    },
    'created:reverse': {
        'sort_on': 'created',
        'sort_order': 'reverse',
    },
    'created:ascending': {
        'sort_on': 'created',
        'sort_order': 'ascending',
    },
    'modified:reverse': {
        'sort_on': 'modified',
        'sort_order': 'reverse',
    },
    'sortable_title:ascending': {
        'sort_on': 'sortable_title',
        'sort_order': 'ascending',
    },
    'sortable_title:reverse': {
        'sort_on': 'sortable_title',
        'sort_order': 'reverse',
    },
}

def _list(val):
    if type(val) not in (list, set, tuple):
        val = [val]
    return val


def _query_val(val):
    if isinstance(val, dict):
        if 'query' in val:
            val = val['query']
    return _list(val)


class DefaultView(BaseTileView):
    name = 'default'
    preview = '++plone++castle/images/previews/querylisting/default.png'
    order = 0
    index = ViewPageTemplateFile('templates/querylisting/default.pt')
    tile_name = 'querylisting'


class DefaultNaturalView(BaseTileView):
    name = 'default-natural'
    label = 'Default(Natural image)'
    preview = '++plone++castle/images/previews/querylisting/default.png'
    order = 0
    index = ViewPageTemplateFile('templates/querylisting/default-natural.pt')
    tile_name = 'querylisting'


class CompactView(BaseTileView):
    name = 'compact'
    preview = '++plone++castle/images/previews/querylisting/compact.png'
    order = 1
    index = ViewPageTemplateFile('templates/querylisting/compact.pt')
    tile_name = 'querylisting'


class GridView(BaseTileView):
    name = 'grid'
    preview = '++plone++castle/images/previews/querylisting/grid.png'
    order = 2
    index = ViewPageTemplateFile('templates/querylisting/grid.pt')
    tile_name = 'querylisting'


class FiveGridView(BaseTileView):
    name = 'five-grid'
    label = 'Five Column Grid'
    preview = '++plone++castle/images/previews/querylisting/grid.png'
    order = 3
    index = ViewPageTemplateFile('templates/querylisting/five-grid.pt')
    tile_name = 'querylisting'


class TiledView(BaseTileView):
    name = 'tiled'
    preview = '++plone++castle/images/previews/querylisting/tiled.png'
    order = 3
    index = ViewPageTemplateFile('templates/querylisting/tiled.pt')
    tile_name = 'querylisting'


class TaggedView(BaseTileView):
    name = 'tagged'
    preview = '++plone++castle/images/previews/querylisting/tagged.png'
    order = 5
    index = ViewPageTemplateFile('templates/querylisting/tagged.pt')
    tile_name = 'querylisting'


class TagFilterView(BaseTileView):
    name = 'tag-filter'
    preview = '++plone++castle/images/previews/querylisting/tag-filter.png'
    order = 5
    index = ViewPageTemplateFile('templates/querylisting/tagfilter.pt')
    tile_name = 'querylisting'


class BlogView(BaseTileView):
    name = 'blog'
    order = 5
    index = ViewPageTemplateFile('templates/querylisting/blog.pt')
    tile_name = 'querylisting'


class ArticleView(BaseTileView):
    name = 'article'
    label = 'Article'
    preview = '++plone++castle/images/previews/querylisting/article.png'
    order = 3
    index = ViewPageTemplateFile('templates/querylisting/article.pt')
    tile_name = 'querylisting'

    def render_item(self, item):
        obj = item.getObject()

        feed = SearchFeed(api.portal.get())
        adapter = queryMultiAdapter((obj, feed), IFeedItem)

        if adapter is not None:
            content = adapter.render_content_core().strip()
            if content:
                return self.extract_content(content)

        return self.render_legacy_content(obj)

    def extract_content(self, html):
        dom = fromstring(html)

        # layout-aware content
        panels = dom.cssselect('[data-panel] > *')
        if panels:
            return ''.join(tostring(el) for el in panels)

        # try old fashioned way... bah!
        core = dom.cssselect('#content-core > *')
        if core:
            return ''.join(tostring(el) for el in core)

        # adapter already returned a fragment or unwrapped content
        return tostring(dom)

    def render_legacy_content(self, obj):
        view = getMultiAdapter((obj, self.request), name='view')
        html = view()

        dom = fromstring(html)
        core = dom.cssselect('#content-core > *')

        if core:
            return ''.join(tostring(el) for el in core)

        return tostring(dom)


class QueryListingTile(BaseTile, DisplayTypeTileMixin):
    implements(IPersistentTile)

    display_type_name = 'querylisting'
    display_type_default = 'default'
    display_type_fallback_view = DefaultView

    query_attrs = ('SearchableText', 'Subject', 'sort_on', 'Title')
    mapped_tags = set([
        'Flyer',
        'Handbook',
        'Report',
        'Form'
    ])

    def get_tag(self, item):
        # mapping of potential assigned tags and content types
        # these need to be implemented by underlying theme...
        intersect = set(item.Subject) & self.mapped_tags
        if len(intersect) > 0:
            title = list(intersect)[0]
            search_param = '?Subject=' + title
            class_name = 'castle-tag-' + title.lower().replace(' ', '-')
        else:
            title = item.Type
            type_name = item.portal_type
            search_param = '?portal_type=' + type_name
            class_name = 'castle-tag-' + type_name.lower().replace(' ', '-')
        return {
            'url': '%s/@@search%s' % (
                self.site.absolute_url(),
                search_param),
            'className': class_name,
            'title': title
        }

    def get_query(self):
        parsed = parse_query_from_data(self.data, self.context)
        # XXX we're forcing location queries to be depth of 1
        if 'path' in parsed and 'depth' not in parsed['path']:
            parsed['path']['depth'] = 1
        if 'sort_on' not in parsed:
            parsed['sort_on'] = 'effective'  # defaults to this

        if 'selected-year' in self.request.form:
            # need to turn this into a date query
            year = self.request.form['selected-year']
            try:
                start = DateTime(abs(int(year)), 1, 1)
                end = DateTime(int(year) + 1, 1, 1) - 1
                parsed['effective'] = {
                    'query': (start, end),
                    'range': 'min:max'
                }
            except (KeyError, AttributeError, ValueError, TypeError):
                pass

        if self.show_expired:
            parsed['show_all'] = 1
            parsed['show_inactive'] = 1

        return parsed

    @property
    def data(self):
        if 'display_fields' in self.request.form:
            if type(self.request.form['display_fields']) == str:
                fields = self.request.form['display_fields'].split(',')
                self.request.form['display_fields'] = [a.strip() for a in fields if len(a.strip()) > 0]
        thedata = super(QueryListingTile, self).data
        return thedata

    @property
    def display_fields(self):
        df = self.data.get('display_fields', None)
        if df is None:
            df = ('image', 'description')
        return df

    @property
    def limit(self):
        return self.data.get('limit', 20) or 20

    @property
    def show_expired(self):
        should_show = self.data.get('show_expired', False) or None
        return should_show if should_show in [True, False] else False

    @memoize
    def results(self):
        catalog = getToolByName(self.context, 'portal_catalog')

        # there is a special case with Subject queries...
        # subject queries are OR, so if they are in the original query
        # and have a further filter with a different Subject, we need to
        # do some manual filtering. This can be potentially slow....
        # it's an edge case, so hopefully it's okay...
        query = self.get_query()
        form = self.get_form()
        subject_filter = None

        sort_value = form.get('sort_on')
        if sort_value:
            sort_value = unidecode(sort_value)
            if sort_value in SORT_OPTIONS:
                query.update(SORT_OPTIONS[sort_value])
            elif sort_value in catalog._catalog.indexes:
                # keeps legacy direct values such as ?sort_on=created working
                query['sort_on'] = sort_value

        for attr in self.query_attrs:
            if attr == 'sort_on':
                continue
            if form.get(attr):
                val = _list(form.get(attr))
                if attr == 'Subject':
                    if attr in query and len(set(val) & set(_query_val(query[attr]))) > 0:
                        # matches here when subject is in the original query
                        # so we're trying to turn this into an AND query with manual
                        # filtering later
                        subject_filter = val[0]
                    else:
                        query[attr] = val
                else:
                    query[attr] = unidecode(val[0])

        if query.get('sort_on', '') not in catalog._catalog.indexes:
            query['sort_on'] = 'effective'
            query['sort_order'] = 'reverse'

        result = catalog(**query)

        if subject_filter is not None:
            result = [
                item for item in result
                if item.Subject and subject_filter in item.Subject
            ]

        try:
            page = int(form.get('page', 1)) - 1
        except Exception:
            page = 0

        page = max(page, 0)
        start = page * self.limit
        end = start + self.limit

        return {
            'total': len(result),
            'page': page + 1,
            'items': result[start:end]
        }

    def _next_url(self, url, page):
        params = {}
        if '?' in url:
            url, _, params = url.partition('?')
            params = dict(parse_qsl(params))
        params['page'] = page + 1
        return url + '?' + urlencode(params)

    def next_url(self, page):
        return self._next_url(self.view_url, page)

    def get_form(self):
        try:
            return self.request.original_data
        except AttributeError:
            return self.request.form

    @property
    @memoize
    def this_url(self):
        if hasattr(self.context, 'absolute_url'):
            url = '{}/@@{}/{}'.format(
                self.context.absolute_url(), self.__name__, self.id or ''
            )
        else:
            url = ''

        params = {}
        form = self.get_form()
        for attr in self.query_attrs:
            if form.get(attr):
                val = form.get(attr)
                if isinstance(val, list):
                    val = [unidecode(v) for v in val]
                else:
                    val = unidecode(val)
                params[attr] = val
        if len(params) > 0:
            url += '?' + urlencode(params)
        return url

    @property
    def filter_pattern_config(self):
        query_filter = self.data.get('query_filter')
        if query_filter is None:
            query_filter = (
                'show_filter_bar',
                'show_text_filter',
                'show_date_filter'
            )
        config = {
            'tags': self.data.get('available_tags', []) or [],
            'query_filter': query_filter,
        }
        form = self.get_form()
        config['query'] = {}
        for attr in self.query_attrs:
            if form.get(attr):
                config['query'][attr] = form.get(attr)
        if ('Subject' in config['query'] and
                isinstance(config['query']['Subject'], basestring)):
            config['query']['Subject'] = [config['query']['Subject']]

        config['display_type'] = self.data.get('display_type', None)

        out = '{}'
        try:
            config['ajaxResults'] = {
                'url': self.view_url,
                'selector': '#query-results-%s' % self.id or ''
            }

            out = json.dumps(config)
        except UnicodeDecodeError:
            try:
                # try to gracefully smooth over any unicode errors
                out = json.dumps(config, ensure_ascii=False)
            except UnicodeDecodeError:
                # It still didn't work. Let's just return an empty object
                pass
        return out


class IQueryListingTileSchema(model.Schema):

    title = schema.TextLine(
        title=u'Title',
        description=u'Provide title above listing',
        required=False,
        default=None
    )

    form.widget(query=QueryFieldWidget)
    query = schema.List(
        title=u'Base query',
        description=u"This query can be customized based on user selection",
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False
    )

    sort_on = schema.TextLine(
        title=u'Sort on',
        description=u"Sort on this index",
        required=False,
        default=defaults.get('querylisting_tile_sort_on', u'effective')
    )

    sort_reversed = schema.Bool(
        title=u'Reversed order',
        description=u'Sort the results in reverse order',
        required=False,
        default=True
    )

    show_expired = schema.Bool(
        title=u'Show Expired',
        description=u'Include all results, even expired ones',
        required=False,
        default=False,
    )

    limit = schema.Int(
        title=u'Limit',
        description=u'Limit number of search results',
        required=False,
        default=15,
        min=1,
    )

    form.widget(
        'available_tags',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Keywords'
    )
    available_tags = schema.Tuple(
        title=u'Tags',
        description=u'Available tags to select from the query widget',
        value_type=schema.TextLine(),
        required=False,
        missing_value=()
    )

    form.widget('query_filter', CheckBoxFieldWidget)
    query_filter = schema.Tuple(
        title=u'Query Filter',
        description=u'Query filter display options',
        default=(
            'show_filter_bar',
            'show_text_filter',
            'show_date_filter'
        ),
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleTerm('show_filter_bar', 'show_filter_bar', u'Display Filter?'),
                SimpleTerm('show_text_filter', 'show_text_filter', u'Text Field - Search Filter'),
                SimpleTerm('show_date_filter', 'show_date_filter', u'Dropdown - Filter by Year'),
            ])
        )
    )

    form.widget('display_fields', CheckBoxFieldWidget)
    display_fields = schema.Tuple(
        title=u'Display fields',
        description=u'Fields that should show on the listing',
        default=(
            'image',
            'description'
        ),
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleTerm('image', 'image', u'Image'),
                SimpleTerm('date', 'date', u'Publication (Effective) Date'),
                SimpleTerm('eventstartend', 'eventstartend', u'Event Start and End'),
                SimpleTerm('description', 'description', u'Overview/Summary')
            ])
        )
    )

    form.widget('display_type', PreviewSelectFieldWidget,
                tile_name='querylisting')
    display_type = schema.Choice(
        title=u"Display Type",
        source=TileViewsSource('querylisting'),
        default=defaults.get('querylisting_tile_displaytype', u'default')
    )
