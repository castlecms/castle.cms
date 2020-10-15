from castle.cms.caching.purgemanager import PurgeManager
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import requests


class Fastly(PurgeManager):
    def __init__(self):
        super(Fastly, self).__init__()
        registry = getUtility(IRegistry)
        self.fastly_token = registry.get('castle.fastly_token', None)
        self.fastly_service_id = registry.get('castle.fastly_service_id', None)
        self.enabled = (
            self.fastly_token is not None and
            self.fastly_service_id is not None)

    def purge(self, urls):
        url = "https://api.fastly.com/service/%s/purge_all" % self.fastly_service_id
        headers = {
            "accept": "application/json",
            "fastly-key": self.fastly_token
        }

        return requests.request("POST", url, headers=headers)


def get():
    return Fastly()
