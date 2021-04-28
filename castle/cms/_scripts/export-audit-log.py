import argparse
import csv
import logging
import sys

from AccessControl.SecurityManagement import newSecurityManager
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
    parser = argparse.ArgumentParser(
        description='Export Audit Logs to CSV for a specific site')
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    parser.add_argument('--filepath', dest='filepath', default='./exported-audit-data.csv')
    args, _ = parser.parse_known_args()
    return args


def export(args):
    es_custom_index_name_enabled = api.portal.get_registry_record(
        'castle.es_index_enabled', default=False)
    custom_index_value = api.portal.get_registry_record('castle.es_index', default=None)
    index_name = audit.get_index_name(
        site_path=None,
        es_custom_index_name_enabled=es_custom_index_name_enabled,
        custom_index_value=custom_index_value)
    logger.info("exporting from ES index `{}`".format(index_name))

    es = ESConnectionFactoryFactory()()
    query = {"query": {'match_all': {}}}
    countresult = es.count(
        index=index_name,
        body=query)
    size = countresult.get("count", 1000000000)
    logger.info("- {} results being exported".format(size))

    results = es.search(
        index=index_name,
        body=query,
        sort='date:desc',
        size=size)

    logging.info("- writing to `{}`".format(args.filepath))
    with open(args.filepath, 'w') as output:
        writer = csv.writer(output)
        writer.writerow(['date', 'name', 'object', 'path', 'request_uri', 'summary', 'type', 'user'])
        for result in results['hits']['hits']:
            data = result['_source']
            writer.writerow([
                data.get("date", ""),
                data.get("name", ""),
                data.get("object", ""),
                data.get("path", ""),
                data.get("request_uri", ""),
                data.get("summary", ""),
                data.get("type", ""),
                data.get("user", ""),
            ])

    logging.info("- export complete")


def run(app):
    singleton.SingleInstance('exportauditlog')

    args = get_args()

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa
    site = app[args.site_id]
    setSite(site)

    export(args)


if __name__ == '__main__':
    run(app)  # noqa

