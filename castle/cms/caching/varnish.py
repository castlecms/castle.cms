from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import requests
import subprocess

class VarnishPurgeManager(object):
    def __init__(self):
        registry = getUtility(IRegistry)
        self.ssh_root_password = registry.get('castle.csm.va_ssh_root_pass', None)
        self.ssh_password = registry.get('castle.va_ssh_pass', None)
        self.port = registry.get('castle.va_port', None)
        self.address = registry.get('castle.va_address', None)
        self.enabled = (
            self.ssh_password is not None or
            self.ssh_root_password is not None and
            self.port is not None and
            self.address is not None)
        self.site = api.portal.get()
        self.public_url = registry.get('plone.public_url', None)
        if not self.public_url:
            self.public_url = self.site.absolute_url()
        self.site_path = '/' + self.site.virtual_url_path()

    def purge_themes(self):
        generate_vcl_script():
        generate_ssh_command():
        try:
            subprocess.check_call([self.ssh, 'su'
                                   , self.ssh_password, 'su', self.ssh_root_password,
                                   self.vcl_script ">> varnish_theme_destroy.vcl"])
        except Exception as ex:
            
                
    def generate_ssh_command(self):
        if self.address != "localhost":
            self.ssh = ("%s:%s" % self.address, self.port)
        else self.ssh = ''
                
    def generate_vcl_script(self):
        # Generates the vcl scripts for the varnish server
        acl_script = """
        acl purge {
        "localhost";
        }
        """

        vcl_subroutine = """
        sub vcl_recv {

        if (req.method == "PURGETHEME") {
                if (!client.ip ~ purge) {
                        return(synth(405,"Not allowed."));
                }
                return (purge);
        }
}
        """
    

        self.vcl_script =  acl_script + vcl_subroutine
        
