import argparse
import csv
import datetime
import logging
import sys

from AccessControl.SecurityManagement import newSecurityManager
from tendo import singleton
from zope.component.hooks import setSite

from castle.cms import audit
from castle.cms.indexing import hps


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
        help='site id to fetch audit log for')
    parser.add_argument(
        '--filepath', dest='filepath', default='./exported-audit-data.csv',
        help='where to export data in csv format')
    parser.add_argument(
        '--scrolltime', dest='scrolltime', default='2s',
        help='ES scroll time, scroll api is used for ES2.3 compat')
    parser.add_argument('--searchtimeout', dest='searchtimeout', default='10s')
    parser.add_argument('--timeout', dest='timeout', type=float, default=0.5)
    args, _ = parser.parse_known_args()
    return args


def convertunicode(s):
    if isinstance(s, unicode):  # noqa: F821
        return s.encode('utf-8')
    return s


def export(args):
    logger.info("exporting from index `{}`".format(audit.get_index_name()))
    starttime = datetime.datetime.now()

    logger.info("fetching resultset with scroll time of `{}`".format(args.scrolltime))

    query = {"query": {'match_all': {}}}
    size = hps.hps_get_number_of_matches(audit.get_index_name(), query)
    if size < 0:
        logger.info('unknown number of items to export')
    else:
        logger.info("{} items need to be exported".format(size))

    results, _, scroll_id = hps.hps_get_data(
        audit.get_index_name(),
        query,
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
        while len(results) > 0:
            old_scroll_id = scroll_id
            logger.info("writing {} hits for scroll {}".format(len(results), old_scroll_id))
            for result in results:
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
            num += len(results)
            logger.info("{} of {} written".format(num, size))
            logger.info("fetching next scroll...")
            results, _, old_scroll_id = hps.hps_get_scroll(scroll_id=old_scroll_id, scroll=args.scrolltime)

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
