from collective.elasticsearch.es import ElasticSearchCatalog
from collective.elasticsearch.hook import index_batch
from collective.elasticsearch.interfaces import IElasticSettings
from elasticsearch import Elasticsearch
from plone import api
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from zope.component import getUtility


def ESConnectionFactoryFactory(registry=None):
    if registry is None:
        registry = getUtility(IRegistry)
    settings = registry.forInterface(IElasticSettings, check=False)
    hosts = settings.hosts
    opts = dict(
        timeout=getattr(settings, 'timeout', 0.5),
        sniff_on_start=getattr(settings, 'sniff_on_start', False),
        sniff_on_connection_fail=getattr(
            settings, 'sniff_on_connection_fail', False),
        sniffer_timeout=getattr(settings, 'sniffer_timeout', 0.1),
        retry_on_timeout=getattr(settings, 'retry_on_timeout', False)
    )

    def factory():
        return Elasticsearch(hosts, **opts)
    return factory


def index_in_es(obj):
    catalog = api.portal.get_tool('portal_catalog')
    es = ElasticSearchCatalog(catalog)
    if es.enabled:
        index_batch([], {IUUID(obj): obj}, [], es)


def add_indexes(indexes):
    """
    indexes should be a tuple of (name of the index, index type)
    """
    catalog = api.portal.get_tool('portal_catalog')
    for name, _type in indexes.items():
        if name not in catalog.indexes():
            if type(_type) == dict:
                real_type = _type['type']
                del _type['type']
                catalog.addIndex(name, real_type, **_type)
            else:
                catalog.addIndex(name, _type)


def delete_indexes(indexes):
    catalog = api.portal.get_tool('portal_catalog')
    for name in indexes:
        if name in catalog.indexes():
            catalog.delIndex(name)


def add_metadata(metadata):
    catalog = api.portal.get_tool('portal_catalog')
    _catalog = catalog._catalog
    for name in metadata:
        if name not in catalog.schema():
            # override how this works normally to not cause a reindex
            schema = _catalog.schema
            names = list(_catalog.names)
            values = schema.values()
            if values:
                schema[name] = max(values) + 1
            else:
                schema[name] = 0
            names.append(name)

            _catalog.names = tuple(names)
            _catalog.schema = schema


def delete_metadata(metadata):
    catalog = api.portal.get_tool('portal_catalog')
    for name in metadata:
        if name in catalog.schema():
            catalog.delColumn(name)
