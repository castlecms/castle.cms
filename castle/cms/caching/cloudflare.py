from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import plone.api as api
import requests


class PurgeManager(object):
    def __init__(self):
        registry = getUtility(IRegistry)
        self.api_key = registry.get('castle.cf_api_key', None)
        self.email = registry.get('castle.cf_email', None)
        self.zone_id = registry.get('castle.cf_zone_id', None)
        self.enabled = None not in [
            self.api_key,
            self.email,
            self.zone_id,
        ]
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

    def purge(self, urls):
        headers = {
            'X-Auth-Email': self.email,
            "X-Auth-Key": self.api_key,
            'Content-Type': 'application/json'
        }
        url = 'https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache'.format(zone_id=self.zone_id)
        return requests.post(
            url=url,
            headers=headers,
            json={'prefixes': urls},
        )


def get():
    return PurgeManager()
