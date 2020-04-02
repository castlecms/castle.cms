from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests

class VarnishPurgeManager(object):
    def __init__(self):
        registry = getUtility(IRegistry)
        self.ssh_key = registry.get('castle.va_ssh_key', None)
        self.ssh_password = registry.get('castle.va_ssh_pass', None)
        self.port = registry.get('castle.va_port', None)
        self.address = registry.get('castle.va_address', None)
        self.enabled = (
            self.ssh_key is not None and
            self.ssh_password is not None and
            self.port is not None and
            self.address is not None)
        self.site = api.portal.get()
        self.public_url = registry.get('plone.public_url', None)
        if not self.public_url:
            self.public_url = self.site.absolute_url()
        self.site_path = '/' + self.site.virtual_url_path()

    def purge_themes(self):
        pass
