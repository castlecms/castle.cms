from plone import api
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from logging import getLogger

from requests import Request, Session
from requests.exceptions import SSLError

logger = getLogger(__name__)


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
            s = Session()
            req = Request("CASTLE_CMS_PURGE_THEMES", self.address)
            prepped = req.prepare()

            response = s.send(prepped)

            if response.status_code != 200:
                return self.error_handling(response)

            return response

        except SSLError as ex:
            logger.warning("Varnish is not configured with ssl.  "
                           "Please enable ssl on varnish to ensure no mitm attacks. %s" % ex)
        except Exception as ex:
            logger.warning("Something went wrong with the varnish purging. %s" % ex)

    def generate_website(self):
        if self.port is None:
            if self.address.find("https://") == -1:
                self.address = "https://%s%s" % (self.address, self.site_path)
            else:
                self.address = "%s%s" % (self.address, self.site_path)
        else:
            if self.address.find("https://") == -1:
                self.address = "https://%s:%s%s" % (self.address, self.port, self.site_path)
            else:
                self.address = "%s%s" % (self.address, self.port, self.site_path)

    def error_handling(self, response):
        if response.status_code == 401:
            logger.warning("Lack of access, please check the acl theme_purge to ensure your ip is accepted")
        elif response.status_code != 200:
            logger.warning("Some other error happened, "
                           "please check that varnish is using the "
                           "purge_themes subroutine in the vcl_recv subroutine. "
                           "%s" % response)

        return response


def get():
    return VarnishPurgeManager()
