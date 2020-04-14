from plone import api
from plone.app.theming.utils import getAvailableThemes
from plone.app.theming.utils import getTheme
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests


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

        urls = []
        urls.append('%s/%s' % (self.public_url.rstrip('/'), path.lstrip('/')))
        return urls

    def purge(self, urls):
        headers = {
            'X-Auth-Email': self.email,
            "X-Auth-Key": self.api_key,
            'Content-Type': 'application/json'
        }
        return requests.delete(
            'https://api.cloudflare.com/client/v4/zones/%s/purge_cache' % self.zone_id,  # noqa
            headers=headers, data=json.dumps({'files': urls}))

    def purge_themes(self):
       urls = self.get_theme_urls()
       if len(urls) > 30:
           returnurl = []
           for url in urls:

               if len(returnurl) > 30:
                   response = self.purge(returnurl)
                   #If the check isn't 200 then something went wrong with the  
                   if response is not 200:
                       error_handling(response, returnurl)
                   returnurl = []

               returnurl.append(url)

           if len(returnurl) < 30 and len(returnurl) > 0:
                response = self.purge(returnurl)
                if response is not 200:
                    error_handling(response, returnurl)
       else:
           response = self.purge(urls)
           if response is not 200:
               error_handling(response, returnurl)
           
    def get_theme_urls(self):
        urls = []
        themes = getAvailableThemes()
        for theme in themes:
            if theme.development_css is not '': 
                urls.append(self.public_url + theme.development_css)
            if theme.development_js is not '': 
                urls.append(self.public_url + theme.development_js)
            if theme.production_css is not '': 
                urls.append(self.public_url + theme.production_css)
            if theme.production_js is not '':
                urls.append(self.public_url + theme.production_js)
            if theme.tinymce_content_css is not '':
                urls.append(self.public_url + theme.tinymce_content_css)
            if theme.tinymce_styles_css is not '':
                urls.append(self.public_url + theme.tinymce_styles_css)
            for bundle in theme.enabled_bundles:
                urls.append(self.public_url + theme.enabled_bundles)
            for bundle in theme.disabled_bundles:
                urls.append(self.public_url + theme.disabled_bundles)
        return urls

    def error_handling(self, response, urls):
        if response is 200:
            return True
        if response is 401:
            pass
def get():
    return PurgeManager()
