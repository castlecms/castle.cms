"""
This will reindex all objects in the catalog, then remove any dirty id's from
the ES index.

This doesn't just call catalog.manage_catalogRebuild() because we don't want to
just drop the index, then rebuild. Doing so would mean a period of time (for
a very large site, this period might also be large) where search results are
not very reliable or available.

Taking the approach to reindex each object _does_ slow the operation of this
script, but it does mean that an active site won't have it's search hobbled
for the process.
"""
from argparse import ArgumentParser
import datetime
import logging
import sys

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from collective.elasticsearch.es import ElasticSearchCatalog
from collective.elasticsearch.hook import index_batch
from collective.elasticsearch.interfaces import IReindexActive
from plone import api
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.globalrequest import getRequest
from zope.interface import alsoProvides

from castle.cms.cron.utils import setup_site

logger = logging.getLogger("castle.cms")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def get_args():
    parser = ArgumentParser(
        description='Re-index all sites on the instance')
    parser.add_argument(
        '--sites', dest='sites', nargs='*',
        help='if present, then just the sites listed by name will be updated')
    parser.add_argument(
        '--scrolltime', dest='scrolltime', default='2s',
        help='how long to hold a scroll index')
    args, _ = parser.parse_known_args()
    return args


def index_site(site, args):
    setup_site(site)
    catalog = api.portal.get_tool('portal_catalog')
    es = ElasticSearchCatalog(catalog)
    if not es.enabled:
        return

    req = getRequest()
    if req is None:
        logger.critical("could not get fake request")
        sys.exit(1)
    alsoProvides(req, IReindexActive)

    # first we want to get all document ids from elastic
    indexed_uids = []
    query = {
        "query": {
            "match_all": {}
        }
    }
    logger.info("getting UID's from index...")
    result = es.connection.search(
        index=es.index_name,
        scroll=args.scrolltime,
        size=10000,  # maximum result size for es
        body=query,
        # don't want any fields returned, since we just want the ID which maps to a uid
        _source=[]
    )
    totaluids = len(result['hits']['hits'])
    logger.info("extracting ({}, total {}) existing UID's from response...".format(totaluids, totaluids))
    indexed_uids.extend([r['_id'] for r in result['hits']['hits']])
    scroll_id = result['_scroll_id']
    while scroll_id:
        result = es.connection.scroll(
            scroll_id=scroll_id,
            scroll=args.scrolltime
        )
        numresults = len(result['hits']['hits'])
        if numresults == 0:
            break
        totaluids += numresults
        logger.info("extracting ({}, total {}) existing UID's from response...".format(numresults, totaluids))
        indexed_uids.extend([r['_id'] for r in result['hits']['hits']])
        scroll_id = result['_scroll_id']

    logger.info("extracted {} uids".format(totaluids))

    logger.info("scanning catalog...")
    index = {}
    count = 0
    for brain in catalog():
        count += 1
        try:
            ob = brain.getObject()
        except Exception:
            logger.info('Could not get object of %s' % brain.getPath())
            continue
        try:
            uid = IUUID(ob)
            index[uid] = ob
        except TypeError:
            logger.info('Could not get UID of %s' % brain.getPath())
            continue
        if uid in indexed_uids:
            # remove from uids... When all said and done,
            # we'll make sure the uids left are in fact no longer on the
            # system and remove them from es
            indexed_uids.remove(uid)
        if len(index) > 300:
            logger.info('finished indexing %i' % count)
            index_batch([], index, [], es)
            site._p_jar.invalidateCache()
            transaction.begin()
            site._p_jar.sync()
            index = {}
    index_batch([], index, [], es)

    logger.info("removing missing UID's from ES...")
    remove = []
    for uid in indexed_uids:
        brains = catalog(UID=uid)
        if len(brains) == 0:
            remove.append(uid)
    index_batch(remove, {}, [], es)
    logger.info("{} records removed".format(len(remove)))


def run(app):
    singleton.SingleInstance('reindexes')

    args = get_args()

    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))

    starttime = datetime.datetime.now()

    for oid in app.objectIds():
        if args.sites is not None and len(args.sites) > 0 and oid not in args.sites:
            continue
        obj = app[oid]

        if IPloneSiteRoot.providedBy(obj):
            index_site(obj, args)

    endtime = datetime.datetime.now()
    deltatime = endtime - starttime
    logger.info("done. took {}s".format(deltatime.total_seconds()))


if __name__ == '__main__':
    run(app)  # noqa: F821
