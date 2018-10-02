# remove bad archives
# cleanup archive ES entries
# rewrite archive links,images to reference base url
from castle.cms import archival
from castle.cms.cron._crawler import Crawler
from castle.cms.cron.utils import login_as_admin
from castle.cms.files import aws
from castle.cms.interfaces import ICrawlerConfiguration
from collective.elasticsearch.es import ElasticSearchCatalog
from lxml.html import fromstring
from lxml.html import tostring
from plone import api
from plone.registry.interfaces import IRegistry
from urlparse import urlparse
from zope.component import getUtility
from zope.component.hooks import setSite

import argparse
import requests
import transaction


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone')
args, _ = parser.parse_known_args()


def fix_urls(storage, dom):
    for Mover in storage.Movers:
        mover = Mover(dom)
        for el in mover.get_elements():
            url = mover.get_url(el)
            if url is None:
                continue
            # check that the url is an s3 url
            parsed = urlparse(url)
            if parsed.netloc != storage.s3_conn.server_name():
                continue

            original = None
            if 'original-url' in el.attrib:
                # need to maintain the original original
                original = el.attrib['original-url']
            mover.modify(el, aws.swap_url(url))
            if original:
                el.attrib['original-url'] = original


def get_key_from_url(url):
    parsed = urlparse(url)
    # parsed url includes bucket so we strip off bucket to get actual key
    return '/'.join(parsed.path.split('/')[2:])


if __name__ == '__main__':
    login_as_admin(app)  # noqa
    site = app[args.site_id]  # noqa
    setSite(site)

    toremove = {}  # uid: path
    catalog = api.portal.get_tool('portal_catalog')
    registry = getUtility(IRegistry)
    crawler_settings = registry.forInterface(
        ICrawlerConfiguration, prefix='castle')
    es = ElasticSearchCatalog(catalog)
    crawler = Crawler(site, crawler_settings, es)
    storage = archival.Storage(site)
    for key, archive_data in storage.archives.items():
        for url in (archive_data.get('view_url'), archive_data['url']):
            if not url:
                continue
            resp = requests.get(url)
            if 'html' not in resp.headers.get('content-type'):
                continue
            print('processing ' + url)
            dom = fromstring(resp.content)
            prop = dom.cssselect('meta[property="og:url"]')

            fix_urls(storage, dom)
            html = tostring(dom)

            if html == resp.content:
                # no changes, carry out
                continue

            print('saving new version of ' + url)

            path = get_key_from_url(url)

            # now save back
            url = 'https://{host}/{path}'.format(
                host=storage.s3_conn.server_name(),
                path=path)
            key = storage.bucket.get_key(path)
            key.set_contents_from_string(html, headers={
                'Content-Type': 'text/html; charset=utf-8'
            }, replace=True)
            key.make_public()
    app._p_jar.sync()  # noqa
    print('%i needing to be deleted' % len(toremove))
    for uid, content_path in toremove.items():
        data = storage.archives[uid]
        view_url = data.get('view_url')
        if view_url:
            path = get_key_from_url(url)
            storage.bucket.delete_key(path)
        url = data['url']
        path = get_key_from_url(url)
        storage.bucket.delete_key(path)
        del storage.archives[uid]
        del storage.path_to_uid[content_path]

    transaction.commit()
