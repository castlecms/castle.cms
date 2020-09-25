from castle.cms.caching.purgemanager import PurgeManager
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests


class Fastly(PurgeManager):
    def __init__(self):
        super(Fastly, self).__init__()
        registry = getUtility(IRegistry)
        self.fastly_key = registry.get('castle.fastly_key', None)
        self.enabled = (
            self.fastly_key is not None)

    def getUrlsToPurge(self, path):
        return super(StackPath, self).getUrlsToPurge(path)

    def purge(self, url):

        headers = {
            "accept": "application/json",
            "fastly-key": self.fastly_key
        }

        url = "https://api.fastly.com/purge/%s" % url
        return requests.request("POST", url, headers=headers)


def get():
    return Fastly()
