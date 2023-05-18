from AccessControl.SecurityManagement import newSecurityManager
from BTrees.OOBTree import OOBTree
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.defaultpage import get_default_page
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
import transaction
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import setSite

from castle.cms.indexing import hps
from castle.cms.services.google import analytics
from castle.cms.services.google import get_ga4_popularity_data
from castle.cms.social import COUNT_ANNOTATION_KEY
from castle.cms.utils import retriable


def get_results(service, profile_id):
    # Use the Analytics Service Object to query the Core Reporting API
    # for the number of sessions within the past seven days.
    return service.data().ga().get(
        ids='ga:' + profile_id,
        start_date='30daysAgo',
        end_date='today',
        metrics='ga:pageviews',
        sort='-ga:pageviews',
        dimensions='ga:pagePath').execute()


@retriable(sync=True)
def get_popularity(site):
    if not hps.is_enabled():
        return
    
    registry = getUtility(IRegistry)
    ga_id = registry.get('castle.google_analytics_id', None)
    service_key = registry.get('castle.google_api_service_key_file', None)

    if ga_id:
        results = get_ga4_popularity_data(ga_id, service_key)
    else:
        service = analytics.get_ga_service()
        if not service:
            return

        profile = analytics.get_ga_profile(service)
        if not profile:
            return
        results = get_results(service, profile)['rows']

    bulk_data = []
    bulk_size = hps.get_bulk_size()
    conn = hps.get_connection()

    site._p_jar.sync()

    for path, page_views in results:
        path = path.split('?')[0].lstrip('/').replace('/view', '').split('@@')[0]
        ob = site.restrictedTraverse(str(path), None)
        if ob is None:
            continue

        annotations = IAnnotations(ob)
        data = {
            'page_views': int(page_views)
        }
        counts = annotations.get(COUNT_ANNOTATION_KEY, OOBTree())
        counts['page_views'] = int(page_views)
        annotations[COUNT_ANNOTATION_KEY] = counts
        for key, value in counts.items():
            if key in ('page_views',):
                continue
            data[key + '_shares'] = value

        if IPloneSiteRoot.providedBy(ob):
            ob = ob[get_default_page(ob)]

        bulk_data.extend([{
            'update': {
                '_index': conn.get_index_name(),
                '_id': IUUID(ob)
            }
        }, {'doc': data}])

        if len(bulk_data) % bulk_size == 0:
            conn.bulk(index=hps.get_index_name(), body=bulk_data)
            bulk_data = []
            transaction.commit()
            site._p_jar.sync()

    if len(bulk_data) > 0:
        conn.bulk(index=hps.get_index_name(), body=bulk_data)
    transaction.commit()


def run(app):
    singleton.SingleInstance('popularity')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            setSite(obj)
            get_popularity(obj)


if __name__ == '__main__':
    run(app)  # noqa
