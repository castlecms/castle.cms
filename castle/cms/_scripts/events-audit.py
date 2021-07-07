import argparse
import logging
import os
import time

from castle.cms.audit import _record
from castle.cms.constants import AUDIT_CACHE_DIRECTORY
from castle.cms.utils import ESConnectionFactoryFactory
from diskcache import Cache


logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone')
parser.add_argument('--cache-dir', dest='cache_dir', default=AUDIT_CACHE_DIRECTORY)
args, _ = parser.parse_known_args()

site = app[args.site_id]
cache_dir = os.path.relpath(args.cache_dir)
registry = site.portal_registry
conn_factory = ESConnectionFactoryFactory(registry)

while (True):
    cache = Cache(cache_dir)
    if len(cache) == 0:
        cache.close()
        time.sleep(30)
    else:
        with Cache(cache.directory) as reference:
            for key in reference:
                args = (conn_factory, reference[key]['site_path'], reference[key]['data'])
                kwargs = reference[key]['kwargs']
                try:
                    _record(*args, **kwargs)
                    del reference[key]
                except:
                    logger.error('could not add record to audit log')
