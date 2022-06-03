from argparse import ArgumentParser
import csv
from datetime import datetime
import logging
import os
import sys

from AccessControl.SecurityManagement import newSecurityManager
from tendo import singleton
from zope.component.hooks import setSite

from castle.cms import audit
from castle.cms.indexing import hps


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
        return [{
            'date': row[0],
            'name': row[1],
            'object': row[2],
            'path': row[3],
            'request_uri': row[4],
            'summary': row[5],
            'type': row[6],
            'user': row[7],
        } for row in reader]


def doimport(args):
    start_time = datetime.now()

    if not os.path.exists(args.filepath):
        logger.critical("data filepath does not exist: {}".format(args.filepath))
        sys.exit(1)

    if not hps.is_enabled():
        logger.critical('HPS index not enabled on site `{}`'.format(args.site_id))
        sys.exit(1)

    logdata = get_log_data(args.filepath)
    hps.bulk_add_to_index(
        audit.get_index_name(),
        logdata,
        create_with=audit._check_for_index)

    end_time = datetime.now()
    elapsed_time = end_time - start_time
    logger.info('{} entries indexed in {}'.format(len(logdata), elapsed_time))


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
