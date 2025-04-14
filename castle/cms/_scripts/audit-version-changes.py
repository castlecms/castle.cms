from argparse import ArgumentParser
import csv
from datetime import datetime, date
import logging
import os
import sys

from AccessControl.SecurityManagement import newSecurityManager
from collective.elasticsearch.es import ElasticSearchCatalog
from elasticsearch import TransportError
from elasticsearch import helpers
from plone import api
from tendo import singleton
from zope.component.hooks import setSite
from zope.component import getUtility
from plone.registry.interfaces import IRegistry

from castle.cms import audit
from castle.cms.utils import ESConnectionFactoryFactory


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_args():
    parser = ArgumentParser()
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    parser.add_argument('--begin', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), required=False, help="YYYY-MM-DD") # noqa
    parser.add_argument('--end', type=lambda d: datetime.strptime(d, '%Y-%m-%d'), required=False, help="YYYY-MM-DD") # noqa
    parser.add_argument('--change', required=False)
    parser.add_argument('--object', required=False)
    args, _ = parser.parse_known_args()
    return args


def get_query(args):
    filters = [{'term': {'type': 'content'}}, {'term': {'name': 'modified'}}]

    if (args.begin):
        beginTime = args.begin.strftime('%Y-%m-%dT%H:%M:%S')
        filters.append({'range': {'date': {'gte': beginTime}}})
    else: 
        filters.append({'range': {'date': {'gte': str(date.min)}}})
    
    if (args.end): 
        endTime = args.end.strftime('%Y-%m-%dT23:59:59')
        filters.append({'range': {'date': {'lte': endTime}}})
    else:
        endTime = date.today().strftime('%Y-%m-%dT23:59:59')
        filters.append({'range': {'date': {'lte': endTime}}})

    query = {
        "query": {
            'bool': {
                'filter': filters
            }
        }
    }
    
    return query


def do_import(args):
    start_time = datetime.now()

    try:
        catalog = api.portal.get_tool('portal_catalog')
        es_catalog = ElasticSearchCatalog(catalog)
    except Exception:
        logger.critical('Error setting up ElasticSearchCatalog')
        sys.exit(1)

    if not es_catalog.enabled:
        logger.critical('Elasticsearch not enabled on site `{}`'.format(args.site_id))
        return

    es_custom_index_name_enabled = api.portal.get_registry_record(
        'castle.es_index_enabled', default=False)
    custom_index_value = api.portal.get_registry_record('castle.es_index', default=None)
    index_name = audit.get_index_name(
        site_path=None,
        es_custom_index_name_enabled=es_custom_index_name_enabled,
        custom_index_value=custom_index_value)
    logger.info('importing audit log into ES index `{}`'.format(index_name))

    es = ESConnectionFactoryFactory()()
    if not es.indices.exists(index_name):
        logger.info('creating index...')
        try:
            audit._create_index(es, index_name)
        except Exception:
            logging.critical('could not create index `{}`'.format(index_name), exc_info=True)
            sys.exit(1)

    results = es.search(
        index=index_name,
        filter_path=['hits.hits._source'],
        body=get_query(args),
        sort='date:desc',
        size=2000)

    # def changelog(log):
    #     result = ''
    #     for entry in log:
    #         result += entry['path'] + '\n\t' + entry['summary'] + '\n\tDate: ' + entry['date'] + '\n'

    #     return result
    
    audit_log = results['hits']['hits']
    return map(
        lambda hit: hit['_source'],
        audit_log
    )


def do_update(args, log):
    registry = getUtility(IRegistry)
    site_path = '/'.join(api.portal.get().getPhysicalPath())
    from plone.app.uuid.utils import uuidToObject
    for entry in log:
        obj = uuidToObject(entry['object'])
        if not obj:
            # Could not find object
            raise RuntimeError(u"Could not look-up UUID: ", entry['object'])
        elif (entry['object'] == str(args.object)):
            entry['summary'] = 'Change Note Summary: ' + str(args.change)
            entry['date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
            audit._record(ESConnectionFactoryFactory(registry), site_path, entry)
            break


def run(app):
    singleton.SingleInstance('importauditlog')

    args = get_args()

    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))
    site = app[args.site_id]
    setSite(site)

    log = do_import(args)
    #import pdb; pdb.set_trace()
    if (args.change and args.object):
        do_update(args, log)
        log = do_import(args)
        
    print(log)


if __name__ == '__main__':
    run(app)  # noqa: F821
