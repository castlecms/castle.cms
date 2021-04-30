import argparse
import csv
import datetime
import logging
import sys

from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from tendo import singleton
from zope.component.hooks import setSite

from castle.cms import audit
from castle.cms.utils import ESConnectionFactoryFactory


logger = logging.getLogger("castle.cms")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_args():
    parser = argparse.ArgumentParser(
        description='Export Audit Logs to CSV for a specific site')
    parser.add_argument(
        '--site-id', dest='site_id', default=None,
        help='site id to fetch settings from')
    parser.add_argument(
        '--indexname', dest='indexname', default='Castle',
        help='if present, will override any value from the site with --site-id')
    parser.add_argument(
        '--filepath', dest='filepath', default='./exported-audit-data.csv',
        help='where to export data in csv format')
    parser.add_argument(
        '--scrolltime', dest='scrolltime', default='2s',
        help='ES scroll time, scroll api is used for ES2.3 compat')
    parser.add_argument(
        '--host', dest='host', default=None,
        help='ES host to use. if present, all ES settings in arguments will '
             'override site configuration from --site-id')
    parser.add_argument('--searchtimeout', dest='searchtimeout', default='10s')
    parser.add_argument('--timeout', dest='timeout', type=float, default=0.5)
    args, _ = parser.parse_known_args()
    return args


def convertunicode(s):
    if isinstance(s, unicode):  # noqa: F821
        return s.encode('utf-8')
    return s


def export(args):
    if args.indexname is not None:
        index_name = args.indexname
    else:
        es_custom_index_name_enabled = api.portal.get_registry_record(
            'castle.es_index_enabled', default=False)
        custom_index_value = api.portal.get_registry_record('castle.es_index', default=None)
        index_name = audit.get_index_name(
            site_path=None,
            es_custom_index_name_enabled=es_custom_index_name_enabled,
            custom_index_value=custom_index_value)

    logger.info("exporting from ES index `{}`".format(index_name))
    starttime = datetime.datetime.now()

    hostsoverride = None
    optsoverride = None
    if args.host is not None:
        hostsoverride = args.host
        optsoverride = dict(
            timeout=args.timeout,
            sniff_on_start=False,
            sniff_on_connection_fail=False,
        )
    es = ESConnectionFactoryFactory(
        hostsoverride=hostsoverride,
        optsoverride=optsoverride)()
    query = {"query": {'match_all': {}}}
    countresult = es.count(
        index=index_name,
        body=query)
    size = countresult.get("count", -1)
    logger.info("{} results need to be exported (-1 is unknown)".format(size))
    logger.info("fetching resultset with scroll time of `{}`".format(args.scrolltime))
    results = es.search(
        index=index_name,
        body=query,
        sort='date:desc',
        scroll=args.scrolltime,
        size=10000,  # max per search result
        timeout=args.searchtimeout)
    logger.info("writing to `{}` (truncated)".format(args.filepath))
    with open(args.filepath, 'w') as output:
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        logger.info("writing header row...")
        writer.writerow(['date', 'name', 'object', 'path', 'request_uri', 'summary', 'type', 'user'])
        num = 0
        while len(results['hits']['hits']) > 0:
            old_scroll_id = results["_scroll_id"]
            logger.info("writing {} hits for scroll {}".format(
                len(results['hits']['hits']),
                old_scroll_id))
            for result in results['hits']['hits']:
                data = result['_source']
                rowdata = [
                    data.get("date", ""),
                    data.get("name", ""),
                    data.get("object", ""),
                    data.get("path", ""),
                    data.get("request_uri", ""),
                    data.get("summary", ""),
                    data.get("type", ""),
                    data.get("user", ""),
                ]
                rowdata = [convertunicode(a) for a in rowdata]
                writer.writerow(rowdata)
            num += len(results['hits']['hits'])
            logger.info("{} of {} written".format(num, size))
            logger.info("fetching next scroll...")
            results = es.scroll(scroll_id=old_scroll_id, scroll=args.scrolltime)

    endtime = datetime.datetime.now()
    deltatime = endtime - starttime
    logger.info("export complete -- took {}s, exported {} records".format(deltatime.total_seconds(), num))


def run(app):
    singleton.SingleInstance('exportauditlog')

    args = get_args()

    user = app.acl_users.getUser('admin')  # noqa: F821
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa: F821
    if args.site_id is not None:
        site = app[args.site_id]
        setSite(site)

    export(args)


if __name__ == '__main__':
    run(app)  # noqa: F821
