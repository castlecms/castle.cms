import os

from opensearchpy.exceptions import NotFoundError
from wildcard.hps.interfaces import IMappingProvider
from zope.component import getMultiAdapter
from zope.globalrequest import getRequest


CRAWLER_MAPPING = {
    'domain': {
        'type': 'keyword',
        'index': True,
        'store': False
    },
    'sitemap': {
        'type': 'text',
        'index': True,
        'store': False
    },
    'url': {
        'type': 'text',
        'index': False,
        'store': True
    },
    'image_url': {
        'type': 'text',
        'index': False,
        'store': False
    }
}


def index_version():
    ver = os.getenv("CASTLE_CRAWLER_INDEX_VERSION", "1").strip()
    if len(ver) <= 0:
        return "1"
    return ver


# we use a version on the actual index name here to help with reindexing later -- we
# can create an alias that points at this index, and then if we ever need to reindex,
# we can just update the alias to the new index so we don't have downtime and we
# don't have to actually modify any config or source anywhere.
def index_name(site_index_name):
    return '{}_crawler_{}'.format(site_index_name, index_version())


def index_alias_name(site_index_name):
    return '{}_crawler'.format(site_index_name)


def ensure_index_exists(hps, index_name):
    """
    A) make sure index exists
    B) make sure index mapping includes mapped types needed by crawler

    NOTE: if the mapping changes, a new index will need to be generated, and
    then the reindex API operation will need to be used to reindex the
    data, or you'll have to do a full drop of the existing index and then
    initiate a reindex from code and not through the opensearch reindex API
    operation.

    but also note, the index here SHOULD have an alias that gets created as
    well, which should be the primary name used to reference the alias. Which
    should allow for reindexing and then just realiasing so there's no
    downtime or interruption of service, and no change in code or config
    needed.
    """
    if hps.connection.indices.exists(index_name):
        return

    # create the index
    hps.connection.indices.create(index_name)

    # update the mapping for the crawler
    adapter = getMultiAdapter((getRequest(), hps), IMappingProvider)
    mapping = adapter()
    mapping['properties'].update(CRAWLER_MAPPING)
    hps.connection.indices.put_mapping(body=mapping, index=index_name)


def ensure_index_alias_exists(hps, index_alias_name, index_name):
    if hps.connection.indices.exists_alias(index_alias_name):
        return

    hps.connection.indices.put_alias(index_name, index_alias_name)


def url_is_indexed(hps, index_name, url):
    try:
        hps.connection.get(index=index_name, id=url)
        return True
    except NotFoundError:
        return False


def index_doc(hps, index_name, url, data):
    hps.connection.index(index=index_name, id=url, body=data)


def delete_from_index(hps, index_name, url):
    try:
        hps.connection.delete(index=index_name, id=url)
    except NotFoundError:
        pass


def get_all_ids(hps, index_name, domain):
    body = {
        "_source": False,  # don't need any data for documents
        "query": {
            "bool": {
                "filter": {
                    "term": {}
                }
            }
        }
    }
    if domain == "archives":
        body["query"]["bool"]["filter"]["term"]["sitemap"] = "archives"
    else:
        body["query"]["bool"]["filter"]["term"]["domain"] = domain

    _ids = []
    scroll_time = '30s'
    result = hps.connection.search(
        index=index_name,
        scroll=scroll_time,
        size=10000,  # hard limit for opensearch
        body=body)
    _ids.extend([r['_id'] for r in result['hits']['hits']])

    # if there aren't 10k records, at leat, no need to scroll
    if len(result['hits']['hits']) < 10000:
        return _ids

    scroll_id = result['_scroll_id']
    while scroll_id:
        result = hps.connection.scroll(scroll_id=scroll_id, scroll=scroll_time)
        if len(result['hits']['hits']) == 0:
            break
        _ids.extend([r['_id'] for r in result['hits']['hits']])
        scroll_id = result['_scroll_id']

    return _ids
