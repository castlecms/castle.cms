# https://gist.github.com/jonathanmoore/2640302
from AccessControl.SecurityManagement import newSecurityManager
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from castle.cms.social import COUNT_ANNOTATION_KEY
from castle.cms.utils import clear_object_cache
from castle.cms.utils import index_in_es
from castle.cms.utils import retriable
from multiprocessing import Pool
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import defaultpage
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from urllib import quote_plus
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import setSite

import json
import logging
import requests
import time
import transaction

USE_MULTIPROCESSING = True

MATOMO_TOKEN_AUTH = 'castle.matomo_token_auth'
MATOMO_BASE_URL = 'castle.matomo_base_url'
MATOMO_SITE_ID = 'castle.matomo_site_id'

logger = logging.getLogger('castle.cms')


def get_facebook_url_data(urls):
    urls_string = '("%s")' % (
        '","'.join(quote_plus(url) for url in urls)
    )
    access_url = COUNT_URLS['facebook']['url'] % urls_string
    resp = requests.get(access_url).content
    data = json.loads(resp)
    count = 0
    if 'data' not in data:
        return 0
    data = data['data']
    for group in data:
        count += group.get('like_count', 0)
        count += group.get('total_count', 0)
        count += group.get('share_count', 0)
        count += group.get('comment_count', 0)
    return count


def get_matomo_url_data(urls):
    registry = getUtility(IRegistry)
    site_id =  registry.get(MATOMO_SITE_ID, None)
    base_url = registry.get(MATOMO_BASE_URL, None)
    token_auth = registry.get(MATOMO_TOKEN_AUTH, None)
    if site_id is None or site_id == '' or base_url is None  or base_url == '' or token_auth is None \
            or token_auth == '':
        return 0
    total_count = 0
    for url in urls:
        query_url = COUNT_URLS['twitter_matomo']['url']\
                        .replace('%%%BASE_URL%%%', base_url).replace('%%%SITE_ID%%%', site_id).\
                        replace('%%%TOKEN_AUTH%%%', token_auth)\
                    % url
        logger.info('query_url: %s' % query_url)
        resp = requests.get(query_url).content
        datatable = json.loads(resp)
        for d in datatable:
            # TODO also need to handle facebook.com
            if d[u'label'] == u'twitter.com':
                total_count += d[u'nb_visits']
                break
    return total_count


COUNT_URLS = {
    'pinterest': {
        'url': 'http://api.pinterest.com/v1/urls/count.json?callback=foobar&url=%s',
        'slash_matters': True
    },
    'twitter_matomo': {
        'url': '%%%BASE_URL%%%/?module=API&method=Actions.getOutlinks&idSite=%%%SITE_ID%%%&period=year&date=today' 
               '&format=json&token_auth=%%%TOKEN_AUTH%%%&segment=outlinkUrl=@%s',
        'generator': get_matomo_url_data,
    }
}


def _get_url_data(args):
    config, url = args
    access_url = config['url'] % url
    resp = requests.get(access_url).content.lstrip('foobar(').rstrip(')')
    try:
        data = json.loads(resp)
    except:
        return 0
    if data.has_key('count'):
        return data['count']
    elif data.has_key(u'label') and data[u'label'] == u'twitter.com':
        return data[u'nb_visits']
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
                req_urls.append((config, orig_url + '/'))
                req_urls.append((config, _swap_protocol(orig_url + '/')))
        if USE_MULTIPROCESSING:
            results = _req_pool.map(_get_url_data, req_urls)
        else:
            for req_url in req_urls:
                results.append(_get_url_data(req_url))
    return results


def _swap_protocol(url):
    if 'http://' in url:
        return url.replace('http://', 'https://')
    else:
        return url.replace('https://', 'http://')


def _get_urls(urls):
    additional = []
    for url in urls:
        additional.append(_swap_protocol(url))
    urls.extend(additional)
    return urls


_pool = Pool(processes=3)
def _get_counts(urls):
    counts = {}
    type_order = []
    args_list = []
    for type_, config in COUNT_URLS.items():
        counts[type_] = 0
        type_order.append(type_)
        args_list.append((config, urls))

    for idx, type_count in enumerate(map(_get_urls_data, args_list)):
        type_ = type_order[idx]
        for type_count in type_count:
            counts[type_] += type_count
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
def get_social_counts(site, obj, site_url, count=0):
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

    urls = _get_urls(urls)
    counts = _get_counts(urls)

    if not _has_data(counts):
        return
    print '    %s' % counts

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
            get_social_counts(site, obj, site_url, count)
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
