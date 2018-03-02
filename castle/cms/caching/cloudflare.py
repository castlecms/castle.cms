from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope import schema
from zope.interface import Interface

import json
import requests

class ICloudflareSettings(Interface):
    cf_api_key = schema.TextLine(
        title=u'Cloudflare API Key',
        description=u'Setting an API Key here and enabling cache purging '
                    u'activates purging against Cloudflare.',
        required=False
    )

    cf_email = schema.TextLine(
        title=u'Cloudflare Email',
        description=u'One associated with cloudflare api key',
        required=False
    )

    cf_zone_id = schema.TextLine(
        title=u'Cloudflare Zone ID',
        required=False)


class PurgeManager(object):
    def __init__(self):
        registry = getUtility(IRegistry)
        cf_settings = getUtility(IRegistry).forInterface(ICloudflareSettings, check=False)
        self.api_key = cf_settings.cf_api_key
        self.email = cf_settings.cf_email
        self.zone_id = cf_settings.cf_zone_id
        self.enabled = (
            self.api_key is not None and
            self.email is not None and
            self.zone_id is not None)
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

    def purge(self, urls):
        headers = {
            'X-Auth-Email': self.email,
            "X-Auth-Key": self.api_key,
            'Content-Type': 'application/json'
        }
        return requests.delete(
            'https://api.cloudflare.com/client/v4/zones/%s/purge_cache' % self.zone_id,
            headers=headers, data=json.dumps({'files': urls}))

def get():
    return PurgeManager()
