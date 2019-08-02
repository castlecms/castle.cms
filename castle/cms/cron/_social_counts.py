import json
import logging
import time
from multiprocessing import Pool
from urllib import urlencode

import requests

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from castle.cms.social import COUNT_ANNOTATION_KEY
from castle.cms.utils import clear_object_cache, index_in_es, retriable
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import defaultpage
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import setSite


USE_MULTIPROCESSING = True

MATOMO_TOKEN_AUTH = 'castle.matomo_token_auth'
MATOMO_BASE_URL = 'castle.matomo_base_url'
MATOMO_SITE_ID = 'castle.matomo_site_id'

logger = logging.getLogger('castle.cms')


def get_matomo_api_url(url):
    registry = getUtility(IRegistry)
    site_id = registry.get(MATOMO_SITE_ID, None)
    base_url = registry.get(MATOMO_BASE_URL, None)
    token_auth = registry.get(MATOMO_TOKEN_AUTH, None)
    params = {
        'module': 'API',
        'method': 'Actions.getOutlinks',
        'idSite': site_id,
        'period': 'year',
        'date': 'today',
        'format': 'json',
        'token_auth': token_auth,
        'expanded': '1',
        'filter_pattern_recursive': '',
        'u': url
    }
    return '{}/?{}'.format(
        base_url,
        urlencode(params)
    )


_matomo_data_mapping = {
    'facebook_matomo': 'www.facebook.com',
    'twitter_matomo': 'twitter.com'
}


def get_matomo_url_data(urls):
    data = {
        'facebook_matomo': 0,
        'twitter_matomo': 0
    }
    for url in urls:
        query_url = get_matomo_api_url(url)
        resp = requests.get(query_url, timeout=10).content
        datatable = json.loads(resp)
        for d in datatable:
            for key, label in _matomo_data_mapping.items():
                if d['label'] == label:
                    data[key] += d['nb_visits']
    return data


COUNT_TYPES = {
    'pinterest': {
        'url': 'http://api.pinterest.com/v1/urls/count.json?callback=foobar&url=%s',
        'slash_matters': True
    },
    'matomo': {
        'generator': get_matomo_url_data,
    }
}


def _get_url_data(args):
    config, url = args
    access_url = config['url'] % url
    resp = requests.get(access_url).content.lstrip('foobar(').rstrip(')')
    try:
        data = json.loads(resp)
    except ValueError:
        return 0
    if 'count' in data:
        return data['count']
    else:
        return 0


_req_pool = Pool(6)


def _get_urls_data(args):
    results = []
    config, urls = args
    if config.get('generator'):
        results.append(config['generator'](urls))
    else:
        req_urls = []
        for orig_url in urls:
            req_urls.append((config, orig_url))
            if config.get('slash_matters'):
                req_urls.append((config, orig_url.rstrip('/') + '/'))
        if USE_MULTIPROCESSING:
            results = _req_pool.map(_get_url_data, req_urls)
        else:
            for req_url in req_urls:
                results.append(_get_url_data(req_url))
    return results


_pool = Pool(processes=3)


def _get_counts(urls, count_types):
    counts = {}
    for type_, config in count_types.items():
        for result in _get_urls_data((config, urls)):
            if isinstance(result, dict):
                # manually setting keys on social data here
                for key, value in result.items():
                    if key not in counts:
                        counts[key] = 0
                    counts[key] += value
            else:
                if type_ not in counts:
                    counts[type_] = 0
                counts[type_] += result
    return counts


def _merge_counts(one, two):
    for key, count in two.items():
        if key in one:
            one[key] += count
        else:
            one[key] = count
    return one


def _has_data(data):
    found = False
    for key, val in data.items():
        if val > 0:
            found = True
            break
    return found


def _count_diff(existing, new):
    diff = False
    for name, value in new.items():
        if value != existing.get(name):
            diff = True
            break
    return diff


@retriable(sync=True)
def get_social_counts(site, obj, site_url, count_types, count=0):
    counts = {}
    site_path = '/'.join(site.getPhysicalPath())
    obj_path = '/'.join(obj.getPhysicalPath())
    rel_path = obj_path[len(site_path):].strip('/')
    print('Looking up ' + obj_path)

    urls = [site_url.rstrip('/') + '/' + rel_path]
    registry = getUtility(IRegistry)
    if obj.portal_type in registry.get('plone.types_use_view_action_in_listings', []):
        urls.append(urls[0] + '/view')

    container = aq_parent(obj)
    if defaultpage.is_default_page(container, obj):
        container_path = '/'.join(container.getPhysicalPath())
        rel_path = container_path[len(site_path):].strip('/')
        urls.append(site_url.rstrip('/') + '/' + rel_path)

    redirector = getUtility(IRedirectionStorage)
    for redirect in redirector.redirects(obj_path):
        rel_path = redirect[len(site_path):].strip('/')
        urls.append(site_url.rstrip('/') + '/' + rel_path)

    counts = _get_counts(urls, count_types)

    if not _has_data(counts):
        return

    obj._p_jar.sync()
    annotations = IAnnotations(obj)
    existing = annotations.get(COUNT_ANNOTATION_KEY, OOBTree())

    if not _count_diff(existing, counts):
        return

    # XXX check if value different first before transaction!
    existing.update(counts)
    annotations[COUNT_ANNOTATION_KEY] = existing

    transaction.commit()

    index_in_es(obj)
    if count % 200 == 0:
        clear_object_cache(site)


def retrieve(site):
    setSite(site)
    registry = getUtility(IRegistry)
    site_url = registry.get('plone.public_url')
    if not site_url:
        logger.info("No public URL is set; skipping site %s" % site)
        return

    # Which counting strategies should we use?
    count_types = COUNT_TYPES.copy()
    site_id = registry.get(MATOMO_SITE_ID, None)
    base_url = registry.get(MATOMO_BASE_URL, None)
    token_auth = registry.get(MATOMO_TOKEN_AUTH, None)
    if not site_id or not base_url or not token_auth:
        # filter all _matomo count types
        for ctype in list(count_types.keys()):
            if ctype.endswith('_matomo'):
                del count_types[ctype]

    catalog = getToolByName(site, 'portal_catalog')
    count = 0
    for brain in catalog(review_state='published'):
        # we ignore some types...
        if brain.portal_type in ('Image', 'Dashboard',):
            continue
        path = brain.getPath()
        count += 1
        try:
            obj = brain.getObject()
            get_social_counts(site, obj, site_url, count_types, count)
            logger.info('retrieved social stats for: %s' % path)
        except Exception:
            logger.warn('error getting social count totals for: %s' % path,
                        exc_info=True)
        time.sleep(2)


def run(app):
    singleton.SingleInstance('socialcounts')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            retrieve(obj)


if __name__ == '__main__':
    run(app)  # noqa
