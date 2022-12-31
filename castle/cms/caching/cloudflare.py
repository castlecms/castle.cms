from plone import api
from plone.app.theming.utils import getAvailableThemes
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from logging import getLogger

import json
import requests

logger = getLogger(__name__)


class PurgeManager(object):
    def __init__(self):
        registry = getUtility(IRegistry)
        self.api_key = registry.get('castle.cf_api_key', None)
        self.email = registry.get('castle.cf_email', None)
        self.zone_id = registry.get('castle.cf_zone_id', None)
        self.enabled = (
            self.api_key is not None and
            self.email is not None and
            self.zone_id is not None)
        self.site = api.portal.get()
        self.public_url = registry.get('plone.public_url', None)
        if not self.public_url:
            self.public_url = self.site.absolute_url()
        self.site_path = '/' + self.site.virtual_url_path()

    # eventual support more than just CF
    def getUrlsToPurge(self, path):

        # remove virtual hosting stuff
        if '/_vh_' in path:
            path = '/' + path.split('/_vh_')[-1].split('/', 1)[-1]
        if 'VirtualHostRoot' in path:
            path = path.split('VirtualHostRoot')[-1]
        if self.site_path not in ('', '/') and path.startswith(self.site_path):
            path = path[len(self.site_path):]

        path = path.decode('utf-8')

        urls = []
        urls.append(u'%s/%s' % (self.public_url.rstrip('/'), path.lstrip('/')))
        return urls

    def purge(self, urls, unsafe=False):
        headers = {
            'X-Auth-Email': self.email,
            "X-Auth-Key": self.api_key,
            'Content-Type': 'application/json'
        }

        response = requests.delete(
            'https://api.cloudflare.com/client/v4/zones/%s/purge_cache' % self.zone_id,  # noqa
            headers=headers, data=json.dumps({'files': urls}))

        if unsafe is False and response.status_code != 200:
            self.error_handling(response, urls)
        else:
            return response

    def purge_themes(self):
        urls = self.get_theme_urls()
        if len(urls) > 30:
            returnurl = []
            for url in urls:

                if len(returnurl) > 30:
                    response = self.purge(returnurl)
                    returnurl = []

                returnurl.append(url)

            if len(returnurl) < 30 and len(returnurl) > 0:
                response = self.purge(returnurl)
        else:
            response = self.purge(urls)
        return response

    def get_theme_urls(self):
        urls = []
        themes = getAvailableThemes()
        for theme in themes:
            if theme.development_css != '':
                urls.append(self.public_url + theme.development_css)
            if theme.development_js != '':
                urls.append(self.public_url + theme.development_js)
            if theme.production_css != '':
                urls.append(self.public_url + theme.production_css)
            if theme.production_js != '':
                urls.append(self.public_url + theme.production_js)
            if theme.tinymce_content_css != '':
                urls.append(self.public_url + theme.tinymce_content_css)
            if theme.tinymce_styles_css != '':
                urls.append(self.public_url + theme.tinymce_styles_css)
            for bundle in theme.enabled_bundles:
                urls.append(self.public_url + theme.enabled_bundles)
            for bundle in theme.disabled_bundles:
                urls.append(self.public_url + theme.disabled_bundles)
        return urls

    def error_handling(self, response, urls):
        if response.status_code == 200:
            return response
        elif response.status_code == 429:
            logger.warning("Too Many Requests, you have made too many requests to cloudflare.  "
                           "Please wait for 24 hours until calling Cloudflare again.")
        elif response.status_code == 403:
            logger.warning("Authentication error.  Please check authentication settings.")
        elif response.status_code == 401:
            logger.warning("Authorization error, the user doesn't have proper credentials")
        elif response.status_code == 400:
            logger.warning("One or more of the urls are invalid. "
                           "Will now be going through the url list "
                           "one url at a time to purge the valid urls %s" % urls)
            self.error_400_handling(urls)
            return response
        else:
            logger.warning("Some other error occurred.  "
                           "Please check https://api.cloudflare.com/#getting-started-responses "
                           "for possible proper response to the error. %s; %s" % (response, urls))

    def error_400_handling(self, urls):
        failed_urls = 0
        for url in urls:
            response = self.purge(urls, unsafe=True)
            if response.status_code == 400:
                failed_urls += 1
        if failed_urls == len(urls):
            logger.warning("Warning, all of the urls have failed please check on the cloudflare settings.")
        return response


def get():
    return PurgeManager()
