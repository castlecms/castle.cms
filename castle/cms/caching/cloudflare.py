from castle.cms.caching.purgemanager import PurgeManager
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests


class CloudFlare(PurgeManager):
    def __init__(self):
        super(CloudFlare, self).__init__()
        registry = getUtility(IRegistry)
        self.api_key = registry.get('castle.cf_api_key', None)
        self.email = registry.get('castle.cf_email', None)
        self.zone_id = registry.get('castle.cf_zone_id', None)
        self.enabled = (
            self.api_key is not None and
            self.email is not None and
            self.zone_id is not None)

    def getUrlsToPurge(self, path):
        return super(CloudFlare, self).getUrlsToPurge(path)

    def purge(self, urls):
        url = 'https://api.cloudflare.com/client/v4/zones/%s/purge_cache' % self.zone_id
        headers = {
            'X-Auth-Email': self.email,
            "X-Auth-Key": self.api_key,
            'Content-Type': 'application/json'
        }

        return requests.delete(url, headers=headers, data=json.dumps({'files': urls}))


def get():
    return CloudFlare()
