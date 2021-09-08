from argparse import ArgumentParser
import csv
from datetime import datetime
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

from castle.cms import audit
from castle.cms.utils import ESConnectionFactoryFactory


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_args():
    parser = ArgumentParser(
        description='Import Audit Logs from exported CSV into ES')
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    parser.add_argument('--filepath', dest='filepath', default='./exported-audit-data.csv')
    args, _ = parser.parse_known_args()
    return args


def get_log_data(filepath):
    with open(filepath, 'r') as fin:
        reader = csv.reader(fin)
        firstrow = True
        for row in reader:
            if firstrow:
                firstrow = False
                continue
            yield {
                'date': row[0],
                'name': row[1],
                'object': row[2],
                'path': row[3],
                'request_uri': row[4],
                'summary': row[5],
                'type': row[6],
                'user': row[7],
            }


def bulkupdate(es, bulkdata, index_name):
    try:
        helpers.bulk(es, bulkdata)
    except TransportError as ex:
        if 'InvalidIndexNameException' in ex.error:
            try:
                audit._create_index(es, index_name)
            except TransportError:
                return
            helpers.bulk(es, bulkdata)
        else:
            raise ex


def doimport(args):
    start_time = datetime.now()

    if not os.path.exists(args.filepath):
        logger.critical("does not exist: {}".format(args.filepath))
        sys.exit(1)

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

    num = 0
    bulkdata = []
    for log in get_log_data(args.filepath):
        bulkdata.append({
            "_index": index_name,
            "_source": log,
        })
        num += 1
        if num % 10000 == 0:
            logger.info("at {}, performing bulk operation...".format(num))
            bulkupdate(es, bulkdata, index_name)
            bulkdata = []
    logger.info("at {}, performing final bulk operation...".format(num))
    bulkupdate(es, bulkdata, index_name)

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    logger.info('{} entries indexed in {}'.format(num, elapsed_time))


def run(app):
    singleton.SingleInstance('importauditlog')

    args = get_args()

    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))
    site = app[args.site_id]
    setSite(site)

    doimport(args)


if __name__ == '__main__':
    run(app)  # noqa: F821
