import logging

# from opensearch import helpers
from opensearchpy import TransportError
from plone import api
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import _getAuthenticatedUser
from urlparse import urljoin
from urlparse import urlparse
from wildcard.hps.interfaces import IQueryAssembler
from wildcard.hps.opensearch import WildcardHPSCatalog
from zope.component import getMultiAdapter
from zope.component import getUtility
from collective.elasticsearch.es import ElasticSearchCatalog
from collective.elasticsearch.hook import index_batch


logger = logging.getLogger("Plone")


def get_catalog(foraudit=False):
    catalog = api.portal.get_tool('portal_catalog')
    if not foraudit:
        hps = WildcardHPSCatalog(catalog)
    else:
        hps = WildcardHPSCatalog(catalog, envprefix='AUDIT_OPENSEARCH_')
    return hps


def get_connection(foraudit=False):
    hpscat = get_catalog(foraudit=foraudit)
    return hpscat.connection


def get_index_name():
    hpscat = get_catalog()
    return hpscat.index_name


def get_bulk_size():
    hpscat = get_catalog()
    return hpscat.get_setting("bulk_size", 50)


def is_enabled(foraudit=False):
    hpscat = get_catalog(foraudit=foraudit)
    return hpscat.enabled


def health_is_good(foraudit=False):
    conn = get_connection(foraudit=foraudit)
    try:
        return conn.cluster.health()['status'] in ('green', 'yellow')
    except Exception:
        return False


def hps_get_number_of_matches(index_name, query):
    conn = get_connection()
    results = conn.count(index=index_name, body=query)
    return results.get('count', -1)


def hps_get_data(index_name, query, foraudit=False, **kwargs):
    conn = get_connection(foraudit=foraudit)
    results = conn.search(index=index_name, body=query, **kwargs)
    try:
        data = results['hits']['hits']
        total = results['hits']['total']['value']
        scroll_id = results.get('_scroll_id', None)
        return data, total, scroll_id
    except KeyError:
        return [], -1, None


def hps_get_scroll(scroll_id, **kwargs):
    conn = get_connection()
    results = conn.scroll(scroll_id=scroll_id, **kwargs)
    try:
        data = results['hits']['hits']
        total = results['hits']['total']['value']
        scroll_id = results.get('_scroll_id', None)
        return data, total, scroll_id
    except KeyError:
        return [], -1, None


def gen_audit_query(
        field_map_prefix=None, sort=None, sortdir=None,
        schema_version="1", schema_type="castle.cms.audit", instance=None, site=None,
        typeval=None, user=None, content=None, after=None, before=None):

    sortfield = sort
    schemaversionfield = "schema_version"
    schematypefield = "schema_type"
    instancefield = "instance"
    sitefield = "site"
    typefield = "type"
    userfield = "user"
    objectfield = "object"
    datefield = "date"
    if field_map_prefix is not None:
        sortfield = "{}.{}".format(field_map_prefix, sortfield)
        schemaversionfield = "{}.{}".format(field_map_prefix, schemaversionfield)
        schematypefield = "{}.{}".format(field_map_prefix, schematypefield)
        instancefield = "{}.{}".format(field_map_prefix, instancefield)
        sitefield = "{}.{}".format(field_map_prefix, sitefield)
        typefield = "{}.{}".format(field_map_prefix, typefield)
        userfield = "{}.{}".format(field_map_prefix, userfield)
        objectfield = "{}.{}".format(field_map_prefix, objectfield)
        datefield = "{}.{}".format(field_map_prefix, datefield)

    filters = [
        {'match_phrase': {schemaversionfield: schema_version}},
        {'match_phrase': {schematypefield: schema_type}},
        {'match_phrase': {instancefield: instance}},
        {'match_phrase': {sitefield: site}},
    ]

    if typeval is not None and len(typeval) > 0:
        filters.append({'match_phrase': {typefield: typeval}})

    if user is not None and len(user) > 0:
        filters.append({'match_phrase': {userfield: user}})

    if content is not None and len(content) > 0:
        items = content.split(';')
        if len(items) > 0:
            filters.append({'terms': {objectfield: items}})

    if (after is not None and len(after) > 0) or (before is not None and len(before) > 0):
        rangefilter = {'range': {datefield: {}}}
        if after is not None:
            rangefilter['range'][datefield]['gte'] = after
        if before is not None:
            rangefilter['range'][datefield]['lte'] = before
        rangefilter['range'][datefield]['format'] = "strict_date_optional_time"
        filters.append(rangefilter)

    if len(filters) == 0:
        query = {"query": {'match_all': {}}}
    else:
        filters.append({"match_all": {}})
        query = {
            "query": {
                'bool': {
                    'filter': filters
                }
            }
        }

    if sort is not None:
        sortdir = sortdir or "desc"
        sortquery = [{sortfield: {"order": sortdir, "unmapped_type": "boolean"}}]
        query["sort"] = sortquery

    return query


def index_in_es(obj):
    catalog = api.portal.get_tool('portal_catalog')
    es = ElasticSearchCatalog(catalog)
    if es.enabled:
        index_batch([], {IUUID(obj): obj}, [], es)


def get_index_summary(index_name, terms, agg_agg_terms=None, filter_terms=None):
    query = {
        "size": 0,
        "aggregations": {
            "totals": {
                "terms": terms
            }
        }
    }
    if agg_agg_terms is not None:
        query["aggregations"]["totals"]["aggregations"] = {
            "types": {
                "terms": agg_agg_terms
            }
        }
    if filter_terms is not None:
        query["bool"] = {
            "filter": [{"term": filter_terms}]
        }
    try:
        conn = get_connection()
        result = conn.search(index=index_name, body=query)
    except TransportError:
        logger.error("problem getting index summary for {}".format(index_name), exc_info=True)
        return []

    data = result['aggregations']['totals']['buckets']
    return data


def get_search_results(context, request, catalog, search_attributes, page, page_size, query):
    """
    page: int
    page_size: int, max 10000 (opensearch limit)
    query: dict containing key/value pairs for filters/search fields
    """

    # start is used to skip a number of records returned for the query from
    # opensearch. We don't keep a scroll here, or some other mechanism, to make
    # sure the results are 100% the same between results. This is intentional,
    # as we don't mind if the results and pages change a little between searches
    start = (page - 1) * page_size

    site_path = '/'.join(context.getPhysicalPath())
    base_site_url = context.absolute_url()

    return_data = {
        'count': 0,
        'results': [],
        'page': page,
        'suggestions': [],
    }

    # no query parameters means no results
    if len(query) <= 0:
        return return_data

    user = _getAuthenticatedUser(catalog)
    query['allowedRolesAndUsers'] = catalog._listAllowedRolesAndUsers(user)

    # convert the query parameter into a usable opensearch query
    catalog = api.portal.get_tool('portal_catalog')
    hps = WildcardHPSCatalog(catalog)
    index_name = hps.index_name
    query_assembler = getMultiAdapter((request, hps), IQueryAssembler)
    normalized_query, sort_list = query_assembler.normalize(query)
    os_query = query_assembler(normalized_query)

    # if a specific site's crawl data is being queried, exclude non-applicable
    # results from the generated opensearch query
    if 'searchSite' in request.form:
        index_name = '{}_crawler'.format(hps.index_name)
        os_query = os_query['script_score']['query']
        os_query['bool']['filter'] = [
            {
                'term': {
                    'domain': request.form['searchSite'],
                },
            },
        ]

    # final query includes suggestions on SearchableText and specifying a sort
    final_query = {
        'query': os_query,
        'suggest': {
            'SearchableText': {
                'text': query.get('SearchableText', ''),
                'term': {
                    'field': 'SearchableText',
                },
            },
        },
        'sort': sort_list
    }

    # these are parameters to the search endpoint, but not part of the query
    # itself
    os_query_params = {
        'stored_fields': ','.join(search_attributes),
        'from_': start,
        'size': page_size,
    }

    os_results = hps.connection.search(
        index=index_name,
        body=final_query,
        **os_query_params)

    return_data['count'] = os_results.get('hits', {}).get('total', {}).get('value', 0)

    try:
        return_data['suggestions'] = os_results['suggest']['SearchableText'][0]['options']
    except Exception:
        # likely an index or key error, which means no
        # suggestions, which means we already have an empty list
        pass

    # view_types are just types that should have '/view' appended to the path
    # of the url associated with the object
    registry = getUtility(IRegistry)
    view_types = registry.get('plone.types_use_view_action_in_listings', [])

    data = os_results.get('hits', {}).get('hits', {})
    for result in data:
        fields = result['fields']

        # build an item from the current result datum
        item = {}

        # we only care about the given attributes
        for key in search_attributes:
            val = fields.get(key, None)
            # if a value is a list, but it only has one element, reduce it
            # to just the element value
            if val is not None and type(val) == list and len(val) == 1:
                val = val[0]
            item[key] = val

        # either build or parse out the url, base_url, and path for the object
        if 'url' in fields:
            url = fields['url']
            if url is not None and type(url) == list and len(url) == 1:
                url = url[0]

            base_url = url

            parsed_url = urlparse(url)
            path = parsed_url.path
        else:
            path = fields.get('path.path', '')
            if path is not None and type(path) == list and len(path) == 1:
                path = path[0]
            path = path[len(site_path):]
            url = urljoin('{}/'.format(base_site_url), path.lstrip('/'))

            base_url = url

            portal_type = item.get('portal_type', None)
            if portal_type is not None and portal_type in view_types:
                url = '{}/view'.format(url)

        item['review_state'] = 'published'
        item['score'] = result['_score']
        item['url'] = url
        item['base_url'] = base_url
        item['path'] = path

        return_data['results'].append(item)

    return return_data
