import argparse
import time
import logging

from castle.cms.audit import _record
from castle.cms.constants import AUDIT_CACHE_DIRECTORY
from castle.cms.utils import ESConnectionFactoryFactory
from diskcache import Cache
from elasticsearch import TransportError
from plone import api


logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone')
args, _ = parser.parse_known_args()

site = app[args.site_id]
registry = site.portal_registry
conn_factory = ESConnectionFactoryFactory(registry)


while (True):
    cache = Cache(AUDIT_CACHE_DIRECTORY)
    if len(cache) == 0:
        cache.close()
        logger.warn('sleeping for 5 seconds')
        time.sleep(5)
    else:
        with Cache(cache.directory) as reference:
            for key in reference:
                args = (conn_factory, reference[key]['site_path'], key)
                kwargs = reference[key]['kwargs']
                try:
                    logger.warn('Audit Record: %s' % key)
                    _record(*args, **kwargs)
                    del reference[key]
                except:
                    logger.error('could not add record to audit log')
