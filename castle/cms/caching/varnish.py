from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import requests
import subprocess

class VarnishPurgeManager(object):
    def __init__(self):
        registry = getUtility(IRegistry)
        self.port = registry.get('castle.va_port', None)
        self.address = registry.get('castle.va_address', None)
        self.enabled = (
            self.address is not None)
        self.site = api.portal.get()
        self.site_path = '/' + self.site.virtual_url_path()

    def purge_themes(self):
        try:
            self.generate_website()
            subprocess.check_call(["curl", '-X', 'CASTLE_CMS_PURGE_THEMES', self.address])          
        except Exception as ex:
            logger.error("Something Went Wrong with the varnish purging")
            logger.error(ex)

    def generate_website(self):
        if self.port is None:
            self.address = "%s%s" % (self.address, self.site_path)
        else:
            self.address = "%s:%s%s" % (self.address, self.port, self.site_path)
        
def get():
    return VarnishPurgeManager()
