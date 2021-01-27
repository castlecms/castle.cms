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

    def purge(self, urls):
        endpoint = "https://gateway.stackpath.com/cdn/v1/stacks/%s/purge" % self.stack_id
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer %s" % self.stack_token
        }
        purge_errors = False

        for url in urls:
            payload = {"items": [{"url": url}]}
            response = requests.request("POST", endpoint, json=payload, headers=headers)

            if response.status_code != 200:
                purge_errors = True

        return purge_errors


def get():
    return StackPath()
