import argparse
import gzip
import logging
import sys
import time

from DateTime import DateTime
from lxml import etree
from lxml import html
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
import requests
from StringIO import StringIO
from tendo import singleton
from urlparse import urlparse
from zope.component import getUtility

from castle.cms import archival
from castle.cms import cache
from castle.cms.constants import CRAWLED_DATA_KEY
from castle.cms.cron.utils import login_as_admin
from castle.cms.cron.utils import setup_site
from castle.cms.cron.utils import spoof_request
from castle.cms.files import aws
from castle.cms.indexing import hps
from castle.cms.indexing import crawler as hpscrawl
from castle.cms.interfaces import ICrawlerConfiguration
from castle.cms.utils import clear_object_cache


# override normal plone logging and use a configured root logger here
# to capture output to stdout since this is a script that will need to render
# output of logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Crawler(object):
    _meta_properties = {
        'Title': [
            'meta[property="og:title"]',
            'title',
            '.documentFirstHeading',
            'h1'
        ],
        'Description': [
            'meta[property="og:description"]',
        ],
        'created': [
            'meta[name="DC.date.created"]',
            'meta[name="creationDate"]',
            'meta[name="publicationDate"]',
        ],
        'modified': [
            'meta[name="DC.date.modified"]',
            'meta[name="modificationDate"]',
            'meta[name="publicationDate"]',
        ],
        'effective': [
            'meta[name="publicationDate"]',
        ],
        'portal_type': [
            'meta[name="DC.type"]',
            'meta[name="portalType"]',
            'meta[property="og:type"]',
        ],
        'image_url': [
            'meta[property="og:image"]',
        ]
    }
    date_fields = ['created', 'modified', 'effective']
    searchable_text_selector = ','.join([
        '#content p,#content h2,#content h3,#content ul li'
    ])

    def __init__(self, site, settings, hpscatalog):
        self.site = site
        self.settings = settings
        self.hpscatalog = hpscatalog
        self.index_name = hpscrawl.index_alias_name(hps.get_index_name())

        self.site._p_jar.sync()  # sync transactions

        self.data = cache.get_client(CRAWLED_DATA_KEY)

    def crawl_page(self, url):
        logger.info('Indexing ' + url)
        try:
            resp = requests.get(url, headers={
                'User-Agent': self.settings.crawler_user_agent
            })
        except Exception:
            # unable to access the page, remove for now
            return False
        if resp.status_code == 404 or 'html' not in resp.headers.get('content-type', ''):
            # remove from index
            return False
        try:
            dom = html.fromstring(resp.content)
        except etree.XMLSyntaxError:
            # unable to parse html, remove for now
            return False  # lxml has been known to throw this as a bug, maybe use BeautifulSoup
        parsed = urlparse(url)
        data = {
            'url': url,
            'domain': parsed.netloc
        }

        for name, selectors in self._meta_properties.items():
            for selector in selectors:
                result = dom.cssselect(selector)
                if len(result) > 0:
                    result = result[0]
                    if result.attrib.get('content'):
                        data[name] = result.attrib['content']
                        break
                    elif result.text_content().strip():
                        data[name] = result.text.strip()
                        break

        for date_field in self.date_fields:
            val = data.get(date_field)
            if val:
                try:
                    data[date_field] = DateTime(val).ISO8601()
                except Exception:
                    pass

        searchable_text = [
            data.get('Title', ''),
            data.get('Description', '')
        ]
        for el in dom.cssselect(self.searchable_text_selector):
            searchable_text.append(el.text_content())
        data['SearchableText'] = ' '.join(searchable_text)

        return data

    def crawl_archive_url(self, url):
        # archive urls don't need to be reindexed ever, they
        # are in a RO archive
        if hpscrawl.url_is_indexed(self.hpscatalog, self.index_name, url):
            return

        data = self.crawl_page(url)
        if not data:
            return

        data['sitemap'] = 'archives'
        hpscrawl.index_doc(self.hpscatalog, self.index_name, url, data)

    def crawl_archives(self):
        registry = getUtility(IRegistry)
        base_url = registry.get('castle.aws_s3_base_url', None)

        storage = archival.Storage(self.site)
        urls = []
        for _, archive_data in storage.archives.items():
            # archives never need to be re-indexed
            url = archive_data.get('view_url', None) or archive_data['url']
            urls.append(aws.swap_url(url, base_url=base_url))

        existing_urls = hpscrawl.get_all_ids(self.hpscatalog, self.index_name, "archives")
        for _id in set(urls) - set(existing_urls):
            # pages that have not yet been crawled
            try:
                self.crawl_archive_url(_id)
            except Exception:
                logger.error('Error indexing archive url: ' + _id, exc_info=True)

        for _id in set(existing_urls) - set(urls):
            # pages that have been removed from the archive
            hpscrawl.delete_from_index(self.hpscatalog, self.index_name, _id)

    def clean_removed_pages(self, sitemap, crawled_urls):
        parsed = urlparse(sitemap)
        domain = parsed.netloc
        ids = hpscrawl.get_all_ids(self.hpscatalog, self.index_name, domain)
        for _id in set(ids) - set(crawled_urls):
            hpscrawl.delete_from_index(self.hpscatalog, self.index_name, _id)

    def crawl_site_map(self, sitemap, full=False):
        resp = requests.get(sitemap, headers={
            'User-Agent': self.settings.crawler_user_agent
        })
        if resp.status_code != 200:
            logger.error('Not a valid sitemap response for %s' % sitemap)
            return

        self.site._p_jar.sync()  # sync transactions

        try:
            last_crawled = DateTime(self.data[sitemap])
        except Exception:
            # KeyError or date parsing issue just revert to old time
            last_crawled = DateTime('1999/01/01')

        try:
            self.data[sitemap] = DateTime().ISO8601().decode('utf8')
        except Exception:
            # maybe a storage error or something -- we'll just not set a new time
            # if that happens, and the crawler should pick up crawling the object
            # again
            pass

        clear_object_cache(self.site)

        if sitemap.lower().endswith('.gz'):
            sitemap_content = gzip.GzipFile(fileobj=StringIO(resp.content)).read()
        else:
            sitemap_content = resp.content

        dom = etree.fromstring(sitemap_content)
        crawled_urls = []
        for url_node in dom.xpath("//*[local-name() = 'url']"):
            loc = url_node.xpath("*[local-name() = 'loc']")
            if loc:
                loc = loc[0].text.strip()
            else:
                loc = None
            url = loc
            crawled_urls.append(url)

            lastmod = url_node.xpath("*[local-name() = 'lastmod']")
            if lastmod:
                lastmod = lastmod[0].text.strip()
            else:
                lastmod = None
            if lastmod:
                lastmod = DateTime(lastmod)
                if not full and lastmod < last_crawled:
                    continue

            if not url:
                continue
            try:
                interval = self.settings.crawler_interval
            except Exception:
                interval = 0
            time.sleep(interval)
            data = self.crawl_page(url)
            if data is False:
                crawled_urls.remove(url)
                hpscrawl.remove_doc_from_index(self.hpscatalog, self.index_name, url)
            else:
                data['sitemap'] = sitemap
                hpscrawl.index_doc(self.hpscatalog, self.index_name, url, data)
                crawled_urls.append(url)

        self.clean_removed_pages(sitemap, crawled_urls)


def crawl_site(site, full=False):
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ICrawlerConfiguration, prefix='castle')
    if not settings.crawler_active or not settings.crawler_site_maps:
        logger.info("Crawler must first be enabled in Site Setup")
        return False

    if not hps.is_enabled():
        logger.info("WildcardHPS must be enabled in Site Setup to use Crawler")
        return False

    hpscatalog = hps.get_catalog()
    index_name = hpscrawl.index_name(hps.get_index_name())
    index_alias_name = hpscrawl.index_alias_name(hps.get_index_name())
    hpscrawl.ensure_index_exists(hpscatalog, index_name)
    hpscrawl.ensure_index_alias_exists(hpscatalog, index_alias_name, index_name)
    crawler = Crawler(site, settings, hpscatalog)

    if settings.crawler_index_archive:
        crawler.crawl_archives()

    for sitemap in settings.crawler_site_maps:
        try:
            crawler.crawl_site_map(sitemap, full)
        except Exception:
            logger.error('Error crawling site map: %s' % sitemap, exc_info=True)

    return True


def run(app):
    singleton.SingleInstance('crawler')

    app = spoof_request(app)  # noqa
    login_as_admin(app)  # noqa

    parser = argparse.ArgumentParser(
        description="Index configured sites, archives, and sitemaps for high performance search")
    parser.add_argument('--site-id', dest='site_id', default=None)
    parser.add_argument('--partial', dest='partial', action='store_false')

    args, _ = parser.parse_known_args()

    try:
        if args.site_id is not None:
            setup_site(app[args.site_id])
            crawl_site(app[args.site_id])
        else:
            for oid in app.objectIds():
                obj = app[oid]
                if IPloneSiteRoot.providedBy(obj):
                    try:
                        setup_site(obj)
                        obj._p_jar.sync()  # sync transactions
                        crawl_site(obj, not args.partial)
                    except Exception:
                        logger.error('Error crawling site %s' % oid, exc_info=True)
    except KeyError:
        pass
    except Exception:
        logger.error('Error setting up crawling', exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa
