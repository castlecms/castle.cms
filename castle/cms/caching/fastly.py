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
        return super(Fastly, self).getUrlsToPurge(path)

    def purge(self, urls):
        headers = {
            "accept": "application/json",
            "fastly-key": self.fastly_key
        }

        # TODO: Get this request actually figured out, ideally without looping so response will be easier
        for url in urls:
            url = "https://api.fastly.com/purge/%s" % url
            resp = requests.request("POST", url, headers=headers, data=json.dumps({'files': urls}))

        #! response return format?
        return resp


def get():
    return Fastly()
