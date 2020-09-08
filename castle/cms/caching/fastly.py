from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests


class PurgeManager(object):
    def __init__(self):
        registry = getUtility(IRegistry)
        self.fastly_key = registry.get('castle.fastly_key', None)
        self.enabled = (
            self.fastly_key is not None)
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

    def purge(self, url):

        headers = {
            "accept": "application/json",
            "fastly-key": self.fastly_key
        }

        url = "https://api.fastly.com/purge/%s" % url
        return requests.request("POST", url, headers=headers)


def get():
    return PurgeManager()
