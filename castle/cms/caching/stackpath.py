from castle.cms.caching.purgemanager import PurgeManager
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import requests


class StackPath(PurgeManager):
    def __init__(self):
        super(StackPath, self).__init__()
        registry = getUtility(IRegistry)
        self.stack_id = registry.get('castle.sp_stack_id', None)
        self.stack_token = registry.get('castle.sp_token', None)
        self.enabled = (
            self.stack_id is not None and
            self.stack_token is not None)

    def getUrlsToPurge(self, path):
        return super(StackPath, self).getUrlsToPurge(path)

    def purge(self, urls):
        url = "https://gateway.stackpath.com/cdn/v1/stacks/%s/purge" % self.stack_id
        payload = {"items": [
            {
                "url": self.public_url,
                "recursive": True
            }
        ]}
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer %s" % self.stack_token
        }

        return requests.request("POST", url, json=payload, headers=headers)


def get():
    return StackPath()
