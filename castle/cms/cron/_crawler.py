from BTrees.OOBTree import OOBTree
from castle.cms import archival
from castle.cms.constants import CRAWLED_DATA_KEY
from castle.cms.constants import CRAWLED_SITE_ES_DOC_TYPE
from castle.cms.cron.utils import login_as_admin
from castle.cms.cron.utils import setup_site
from castle.cms.cron.utils import spoof_request
from castle.cms.files import aws
from castle.cms.interfaces import ICrawlerConfiguration
from collective.elasticsearch.es import ElasticSearchCatalog
from collective.elasticsearch.interfaces import IMappingProvider
from DateTime import DateTime
from elasticsearch import NotFoundError
from lxml import etree
from lxml import html
from persistent.dict import PersistentDict
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.log import logger
from StringIO import StringIO
from tendo import singleton
from urlparse import urlparse
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.globalrequest import getRequest
from castle.cms.utils import clear_object_cache

import gzip
import requests
import sys
import time
import transaction


CRAWLER_ES_MAPPING = {
    'domain': {
        'type': 'string',
        'index': 'not_analyzed',
        'store': False
    },
    'sitemap': {
        'type': 'string',
        'index': 'not_analyzed',
        'store': False
    },
    'url': {
        'type': 'string',
        'index': 'not_analyzed',
        'store': False
    },
    'image_url': {
        'type': 'string',
        'index': 'not_analyzed',
        'store': False
    }
}

MAX_PAGE_SIZE = 500000000


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

    def __init__(self, site, settings, es):
        self.site = site
        self.settings = settings
        self.es = es
        self.site._p_jar.sync()
        annotations = IAnnotations(site)
        if CRAWLED_DATA_KEY not in annotations:
            annotations[CRAWLED_DATA_KEY] = OOBTree({
                'tracking': PersistentDict()
            })
            transaction.commit()
        self.data = annotations[CRAWLED_DATA_KEY]

    def crawl_page(self, url):
        logger.info('Indexing ' + url)
        resp = requests.get(url, stream=True, headers={
            'User-Agent': self.settings.crawler_user_agent
        })
        if resp.status_code == 404 or \
          'html' not in resp.headers.get('content-type', '') or \
          int(resp.headers.get('content-length', 0)) \
              >= MAX_PAGE_SIZE:
            # remove from index
            return False
        dom = html.fromstring(resp.content)
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

    def exists_in_index(self, url):
        try:
            self.es.connection.get(
                index=self.es.index_name,
                doc_type=CRAWLED_SITE_ES_DOC_TYPE,
                id=url)
            return True
        except NotFoundError:
            return False

    def crawl_archive_url(self, url):
        if self.exists_in_index(url):
            return
        data = self.crawl_page(url)
        if not data:
            return
        data['sitemap'] = 'archives'
        self.es.connection.index(
            index=self.es.index_name,
            doc_type=CRAWLED_SITE_ES_DOC_TYPE,
            id=url,
            body=data
        )

    def crawl_archives(self):
        registry = getUtility(IRegistry)
        base_url = registry.get('castle.aws_s3_base_url', None)

        storage = archival.Storage(self.site)
        urls = []
        for key, archive_data in storage.archives.items():
            # archives do not need to be re-indexed ever.
            # see if the key is in ES, if it is move on
            url = archive_data.get('view_url', archive_data['url'])
            urls.append(aws.swap_url(url, base_url=base_url))

        query = {
            "filtered": {
                "filter": {
                    "term": {
                        "sitemap": 'archives'
                    }
                },
                "query": {"match_all": {}}
            }
        }
        existing_urls = self.get_all_from_es(query)

        for _id in set(urls) - set(existing_urls):
            # pages that have not yet been crawled
            try:
                self.crawl_archive_url(_id)
            except Exception:
                logger.error('Error indexing archive url: ' + _id, exc_info=True)

        for _id in set(existing_urls) - set(urls):
            # pages that have been removed from the archive
            self.delete_from_index(_id)

    def get_all_from_es(self, query):
        _ids = []
        page_size = 700
        result = self.es.connection.search(
            index=self.es.index_name,
            doc_type=CRAWLED_SITE_ES_DOC_TYPE,
            scroll='30s',
            size=page_size,
            fields=[],
            body={
                "query": query
            })
        _ids.extend([r['_id'] for r in result['hits']['hits']])
        scroll_id = result['_scroll_id']
        while scroll_id:
            result = self.es.connection.scroll(
                scroll_id=scroll_id,
                scroll='30s'
            )
            if len(result['hits']['hits']) == 0:
                break
            _ids.extend([r['_id'] for r in result['hits']['hits']])
            scroll_id = result['_scroll_id']
        return _ids

    def clean_removed_pages(self, sitemap, crawled_urls):
        parsed = urlparse(sitemap)
        domain = parsed.netloc
        query = {
            "filtered": {
                "filter": {
                    "term": {
                        "domain": domain
                    }
                },
                "query": {"match_all": {}}
            }
        }
        ids = self.get_all_from_es(query)
        for _id in set(ids) - set(crawled_urls):
            # what's left are pages we don't care about anymore
            self.delete_from_index(_id)

    def delete_from_index(self, url):
        self.es.connection.delete(
            index=self.es.index_name,
            doc_type=CRAWLED_SITE_ES_DOC_TYPE,
            id=url)

    def crawl_site_map(self, sitemap, full=False):
        resp = requests.get(sitemap, headers={
            'User-Agent': self.settings.crawler_user_agent
        })
        if resp.status_code != 200:
            logger.error('Not a valid sitemap response for %s' % sitemap)
            return

        self.site._p_jar.sync()
        if sitemap in self.data['tracking']:
            last_crawled = DateTime(self.data['tracking'][sitemap])
        else:
            last_crawled = DateTime('1999/01/01')

        self.data['tracking'][sitemap] = DateTime().ISO8601().decode('utf8')
        transaction.commit()
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
                try:
                    self.es.connection.delete(
                        index=self.es.index_name,
                        doc_type=CRAWLED_SITE_ES_DOC_TYPE,
                        id=url)
                except NotFoundError:
                    pass
            else:
                data['sitemap'] = sitemap
                self.es.connection.index(
                    index=self.es.index_name,
                    doc_type=CRAWLED_SITE_ES_DOC_TYPE,
                    id=url,
                    body=data
                )
                crawled_urls.append(url)

        self.clean_removed_pages(sitemap, crawled_urls)


def crawl_site(site, full=False):
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ICrawlerConfiguration, prefix='castle')
    if not settings.crawler_active or not settings.crawler_site_maps:
        return False

    catalog = api.portal.get_tool('portal_catalog')
    es = ElasticSearchCatalog(catalog)
    if not es.enabled:
        return False

    # check index type is mapped, create if not
    try:
        es.connection.indices.get_mapping(
            index=es.index_name,
            doc_type=CRAWLED_SITE_ES_DOC_TYPE)
    except NotFoundError:
        # need to add it
        adapter = getMultiAdapter((getRequest(), es), IMappingProvider)
        mapping = adapter()
        mapping['properties'].update(CRAWLER_ES_MAPPING)
        es.connection.indices.put_mapping(
            doc_type=CRAWLED_SITE_ES_DOC_TYPE,
            body=mapping,
            index=es.index_name)

    crawler = Crawler(site, settings, es)

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

    count = 0

    while True:
        try:
            if 'site-id' in sys.argv:
                siteid = sys.argv['site-id']
                setup_site(app[siteid])
                crawl_site(app[siteid])  # noqa
            else:
                for oid in app.objectIds():  # noqa
                    obj = app[oid]  # noqa
                    if IPloneSiteRoot.providedBy(obj):
                        try:
                            setup_site(obj)
                            obj._p_jar.sync()
                            crawl_site(obj, count % 10 == 0)
                        except Exception:
                            logger.error('Error crawling site %s' % oid, exc_info=True)
        except KeyError:
            pass
        except Exception:
            logger.error('Error setting up crawling', exc_info=True)

        logger.info('Waiting to crawl again')
        time.sleep(10 * 60)
        count += 1


if __name__ == '__main__':
    run(app)  # noqa
