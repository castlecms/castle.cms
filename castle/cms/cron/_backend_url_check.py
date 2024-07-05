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
import plone.api as api
from zope.globalrequest import getRequest

from Products.CMFCore.interfaces import IContentish
from castle.cms.browser.content.backendurls import BackendUrlUtils
# override normal plone logging and use a configured root logger here
# to capture output to stdout since this is a script that will need to render
# output of logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# class Crawler(object):

#     def __init__(self, site):
#         self.site = site
#         # self.settings = settings
#         # self.hpscatalog = hpscatalog
#         # self.index_name = hpscrawl.index_alias_name(hps.get_index_name())

#         self.site._p_jar.sync()  # sync transactions

#         # self.data = cache.get_client(CRAWLED_DATA_KEY)

UNSET = object()

def check_object_views(site):
    errors = []
    invalid_objects = []
    backend_url_utils = BackendUrlUtils()
    content_brains = api.content.find(object_provides=IContentish)
    for content_brain in content_brains:
        url = UNSET
        content_object = UNSET
        view = UNSET
        html = UNSET
        invalid_backend_urls = UNSET
        try:
            url = getattr(content_brain, 'getURL', lambda: 'UNKNOWN URL')()
            logger.info('checking brain at {}'.format(url))
            content_object = content_brain.getObject()
            logger.info('got content object {}'.format(content_object))
            view = api.content.get_view(
                name='view',
                context=content_object,
                request=getRequest(),
            )
            logger.info('got view for {}'.format(content_object))
            html = view()
            logger.info('got html for {}'.format(content_object))
            invalid_backend_urls = backend_url_utils.get_invalid_backend_urls_found(html)
            if len(invalid_backend_urls) > 0:
                logger.warn('There were backend urls found in the html')
                logger.warn('Backend urls found: {}'.format(repr(invalid_backend_urls)))
                logger.warn('View searched for: {}'.format(content_object))
                invalid_objects.append(content_object)
        except Exception:
            error = {}
            if url is not UNSET:
                error['url'] = url
            if content_object is not UNSET:
                error['content_object'] = repr(content_object)
            if invalid_backend_urls is not UNSET:
                error['invalid_backend_urls'] = repr(invalid_backend_urls)
            errors.append(error)
            logger.error('Error checking object view. Continuing')
            continue



def run(app):
    singleton.SingleInstance('backend_url_check')

    app = spoof_request(app)
    login_as_admin(app)

    parser = argparse.ArgumentParser(
        description="Index configured sites, archives, and sitemaps for high performance search")
    parser.add_argument('--site-id', dest='site_id', default=None)

    args, _ = parser.parse_known_args()
    import pdb; pdb.set_trace()
    # try:
    if args.site_id is not None:
        site = app[args.site_id]
        setup_site(app[args.site_id])

        check_object_views(app[args.site_id])
        # else:
        #     for oid in app.objectIds():
        #         obj = app[oid]
        #         if IPloneSiteRoot.providedBy(obj):
        #             try:
        #                 setup_site(obj)
        #                 # obj._p_jar.sync()  # sync transactions
        #                 check_object_views(obj)
        #             except Exception:
        #                 logger.error('Error crawling site %s' % oid, exc_info=True)
    # except KeyError:
    #     pass
    # except Exception:
    #     logger.error('Error setting up crawling', exc_info=True)


if __name__ == '__main__':
    run(app)
