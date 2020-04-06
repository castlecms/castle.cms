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
        self.port = registry.get('castle.va_port', "22")
        self.address = registry.get('castle.va_address', None)
        self.is_ssh = registry.get('castle.va_is_ssh', False)
        self.enabled = (
            self.ssh_password is not None or
            self.ssh_root_password is not None and
            (self.address is not None or
             self.is_ssh))
        self.site = api.portal.get()
        self.public_url = registry.get('plone.public_url', None)
        if not self.public_url:
            self.public_url = self.site.absolute_url()
        self.site_path = '/' + self.site.virtual_url_path()

    def purge_themes(self):
        generate_vcl_script()
        generate_ssh_command()
        try:
            subprocess.check_call([self.ssh, self.vcl_script + ">> varnish_theme_destroy.vcl"])
            vcl_script_exists = subprocess.check_output([self.ssh, "varnishctl"])
        except Exception as ex:
            logger.error("Something Went Wrong with the varnish purging")
            logger.error(ex)
                
    def generate_ssh_command(self):
        if self.is_ssh:
            self.ssh = "%s -p %s" % (self.address, self.port)
        else:
            self.ssh = ""
        if self.ssh_password is None:
            self.ssh_password = ""

        self.ssh = self.ssh + self.ssh_password + 'su' + self.ssh_root_password
                
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
                return (ban("obj.http.x-url ~ \/\+\+.*\+\+"));
        }
}
        """
    

        self.vcl_script =  acl_script + vcl_subroutine
        

def get():
    return VarnishPurgeManager()
