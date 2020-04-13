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
       return self.purge(urls)

    def get_theme_urls(self):
        import pdb; pdb.set_trace()
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
        return urls

        
def get():
    return PurgeManager()
