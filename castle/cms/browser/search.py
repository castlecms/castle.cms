from castle.cms.interfaces import ICrawlerConfiguration
from castle.cms.utils import get_public_url
from castle.cms.indexing import hps

from DateTime import DateTime
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.resources import add_resource_on_request
from Products.Five import BrowserView
from urlparse import urlparse
from zope.component import getUtility
import dateutil.parser

import datetime
import json
import Missing


def custom_json_handler(obj):
    if obj == Missing.Value:
        return None
    if type(obj) in (datetime.datetime, datetime.date):
        return obj.isoformat()
    if type(obj) == DateTime:
        return obj.ISO8601()
    return obj


class Search(BrowserView):
    def __call__(self):
        # utility function to add resource to rendered page
        add_resource_on_request(self.request, 'castle-components-search')
        return super(Search, self).__call__()

    @property
    def options(self):
        search_types = [
            {
                'id': 'images',
                'label': 'Image',
                'query': {
                    'portal_type': 'Image'
                }
            },
            {
                'id': 'page',
                'label': 'Page',
                'query': {
                    'portal_type': ['Document', 'Folder']
                }
            }
        ]

        ptypes = api.portal.get_tool('portal_types')
        allow_anyway = ['Audio']
        for type_id in ptypes.objectIds():
            if type_id in ('Link', 'Document', 'Folder'):
                continue
            _type = ptypes[type_id]
            if not _type.global_allow and type_id not in allow_anyway:
                continue
            search_types.append({
                'id': type_id.lower(),
                'label': _type.title,
                'query': {
                    'portal_type': type_id
                }
            })

        additional_sites = []
        registry = getUtility(IRegistry)
        settings = registry.forInterface(ICrawlerConfiguration, prefix='castle')
        if hps.is_enabled() and settings.crawler_active and settings.crawler_site_maps:
            result = hps.get_index_summary(hps.get_index_name(), dict(field="domain"))
            for res in result:
                site_name = res.get('key')
                if '.' not in site_name or 'amazon' in site_name:
                    continue
                additional_sites.append(site_name)

        parsed = urlparse(get_public_url())
        return json.dumps({
            'searchTypes': sorted(search_types, key=lambda st: st['label']),
            'additionalSites': sorted(additional_sites),
            'currentSiteLabel': parsed.netloc,
            'searchHelpText': api.portal.get_registry_record('castle.search_page_help_text', None),
        })

    @property
    def search_url(self):
        if api.user.is_anonymous():
            try:
                url = api.portal.get_registry_record('castle.searchurl')
                if url:
                    return url
            except Exception:
                pass
        return '%s/@@searchajax' % (
            self.context.absolute_url()
        )


_search_attributes = [
    'Title',
    'Description',
    'Subject',
    'contentType',
    'created',
    'modified',
    'effective',
    'hasImage',
    'is_folderish',
    'portal_type',
    'review_state',
    'path.path'
]

_valid_params = [
    'SearchableText',
    'portal_type',
    'Subject',
    'Subject:list',
    'after',
    'sort_on',
    'sort_order'
]


class SearchAjax(BrowserView):

    def __call__(self):
        self.catalog = api.portal.get_tool('portal_catalog')
        self.request.response.setHeader('Content-type', 'application/json')

        query = {}
        for name in _valid_params:
            real_name = name
            if real_name.endswith(':list'):
                real_name = real_name[:-len(':list')]
            if self.request.form.get(name):
                query[real_name] = self.request.form[name]
            elif self.request.form.get(name + '[]'):
                query[real_name] = self.request.form[name + '[]']

        if query.get('after'):
            if query.get('sort_on') not in ('effective', 'modified', 'created'):
                sort_on = query['sort_on'] = 'effective'
            else:
                sort_on = query['sort_on']
            try:
                date = dateutil.parser.parse(query.pop('after'))
                start = DateTime(date)
                query[sort_on] = {
                    'query': start,
                    'range': 'min'
                }
            except (KeyError, AttributeError, ValueError, TypeError):
                pass

        query['review_state'] = 'published'

        registry = getUtility(IRegistry)
        if not registry.get('plone.allow_public_in_private_container', False):
            query['has_private_parents'] = False
        query['exclude_from_search'] = False

        try:
            page_size = int(self.request.form.get('pageSize'))
        except Exception:
            page_size = 20
        page_size = min(page_size, 50)
        try:
            page = int(self.request.form.get('page'))
        except Exception:
            page = 1

        if hps.is_enabled():
            return self.get_hps_results(page, page_size, query)
        else:
            return self.get_results(page, page_size, query)

    def get_results(self, page, page_size, query):
        # regular plone search
        site_path = '/'.join(self.context.getPhysicalPath())
        start = (page - 1) * page_size
        end = start + page_size
        catalog = api.portal.get_tool('portal_catalog')
        raw_results = catalog(**query)
        items = []

        registry = getUtility(IRegistry)
        view_types = registry.get('plone.types_use_view_action_in_listings', [])

        for brain in raw_results[start:end]:
            attrs = {}
            for key in _search_attributes:
                attrs[key] = getattr(brain, key, None)
            url = base_url = brain.getURL()
            if brain.portal_type in view_types:
                url += '/view'
            attrs.update({
                'path': brain.getPath()[len(site_path):],
                'base_url': base_url,
                'url': url
            })
            items.append(attrs)

        return json.dumps({
            'count': len(raw_results),
            'results': items,
            'page': page,
            'suggestions': []
        }, default=custom_json_handler)

    def get_hps_results(self, page, page_size, query):
        # returns json:
        #   - count -- total hits
        #   - results -- list of items:
        #       - review_state -- always 'published'
        #       - score
        #       - path
        #       - base_url
        #       - url
        #   - page
        #   - suggestions -- list of objects from opensearch

        results = hps.get_search_results(
            self.context,
            self.request,
            self.catalog,
            _search_attributes,
            page,
            page_size,
            query)

        return json.dumps(results, default=custom_json_handler)

