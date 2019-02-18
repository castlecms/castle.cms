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

        return parsed

    @property
    def display_fields(self):
        df = self.data.get('display_fields', None)
        if df is None:
            df = ('image', 'description')
        return df

    @property
    def limit(self):
        return self.data.get('limit', 20) or 20

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
        for attr in self.query_attrs:
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

        result = catalog(**query)
        if subject_filter is not None:
            # special case where we have to further filter...
            result = [item for item in result
                      if item.Subject and subject_filter in item.Subject]
        try:
            form = self.get_form()
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
        return self._next_url(self.this_url, page)

    def get_form(self):
        try:
            return self.request.original_data
        except AttributeError:
            return self.request.form

    @property
    @memoize
    def this_url(self):
        url = '{}/@@{}/{}'.format(
            self.context.absolute_url(), self.__name__, self.id or ''
        )
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
        config = {
            'tags': self.data.get('available_tags', []) or []
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
                'url': self.this_url,
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
