from castle.cms.caching.purgemanager import PurgeManager
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import requests


class Fastly(PurgeManager):
    def __init__(self):
        super(Fastly, self).__init__()
        registry = getUtility(IRegistry)
        self.fastly_token = registry.get('castle.fastly_token', None)
        self.enabled = self.fastly_token is not None

    def purge(self, urls):
        headers = {
            "accept": "application/json",
            "fastly-key": self.fastly_token
        }
        purge_errors = False

        for url in urls:
            endpoint = "https://api.fastly.com/purge/%s" % url
            response = requests.request("POST", endpoint, headers=headers)

            if response.status_code != 200:
                purge_errors = True

        return purge_errors


def get():
    return Fastly()
