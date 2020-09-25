from castle.cms.caching.purgemanager import PurgeManager
from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests


class StackPath(PurgeManager):
    def __init__(self):
        super(StackPath, self).__init__()
        registry = getUtility(IRegistry)
        self.stack_id = registry.get('castle.sp_stack_id', None)
        self.enabled = (
            self.stack_id is not None)

    def getUrlsToPurge(self, path):
        return super(StackPath, self).getUrlsToPurge(path)

    def purge(self, urls):
        url = "https://gateway.stackpath.com/cdn/v1/stacks/%s/purge" % self.stack_id
        headers = {
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        return requests.request("POST", url, json=json.dumps({'files': urls}), headers=headers)


def get():
    return StackPath()
