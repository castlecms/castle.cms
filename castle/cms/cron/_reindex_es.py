import logging

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from castle.cms.cron.utils import setup_site
from collective.elasticsearch.es import ElasticSearchCatalog
from collective.elasticsearch.hook import index_batch
from collective.elasticsearch.interfaces import IReindexActive
from plone import api
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.globalrequest import getRequest
from zope.interface import alsoProvides

logger = logging.getLogger('castle.cms')


def index_site(site):
    setup_site(site)
    catalog = api.portal.get_tool('portal_catalog')
    es = ElasticSearchCatalog(catalog)
    if not es.enabled:
        return

    req = getRequest()
    assert req is not None
    alsoProvides(req, IReindexActive)

    # first we want to get all document ids from elastic
    page_size = 700
    ids = []
    result = es.connection.search(
        index=es.index_name, doc_type=es.doc_type,
        scroll='30s',
        size=page_size,
        fields=[],
        body={
            "query": {
                "match_all": {}
            }
        })
    ids.extend([r['_id'] for r in result['hits']['hits']])
    scroll_id = result['_scroll_id']
    while scroll_id:
        result = es.connection.scroll(
            scroll_id=scroll_id,
            scroll='30s'
        )
        if len(result['hits']['hits']) == 0:
            break
        ids.extend([r['_id'] for r in result['hits']['hits']])
        scroll_id = result['_scroll_id']

    index = {}
    count = 0
    for brain in catalog():
        count += 1
        # go through each object and reindex using bulk setting
        try:
            ob = brain.getObject()
        except Exception:
            print('Could not get object of %s' % brain.getPath())
            continue
        try:
            uid = IUUID(ob)
            index[uid] = ob
        except TypeError:
            print('Could not get UID of %s' % brain.getPath())
            continue
        if uid in ids:
            # remove from uids... When all said and done,
            # we'll make sure the uids left are in fact no longer on the
            # system and remove them from es
            ids.remove(uid)
        if len(index) > 300:
            print('finished indexing %i' % count)
            index_batch([], index, [], es)
            site._p_jar.invalidateCache()  # noqa
            transaction.begin()
            site._p_jar.sync()  # noqa
            index = {}
    index_batch([], index, [], es)

    remove = []
    for uid in ids:
        brains = catalog(UID=uid)
        if len(brains) == 0:
            remove.append(uid)
    index_batch(remove, {}, [], es)


def run(app):
    singleton.SingleInstance('reindexes')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            index_site(obj)


if __name__ == '__main__':
    run(app)  # noqa
