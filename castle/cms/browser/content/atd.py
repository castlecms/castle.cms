from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import ITinyMCESchema
from Products.CMFPlone.interfaces.atd import IATDProxyView
from zope.component import getUtility
from zope.interface import implements

import requests


class ATDProxyView(object):
    """ Proxy for the 'After the Deadline' spellchecker
    """
    implements(IATDProxyView)

    def checkDocument(self):
        """ Proxy for the AtD service's checkDocument function
            See http://www.afterthedeadline.com/api.slp for more info.
        """
        registry = getUtility(IRegistry)
        settings = registry.forInterface(
            ITinyMCESchema, prefix="plone", check=False)
        if settings.libraries_spellchecker_choice != 'AtD':
            return 'atd not enabled'

        tool = getToolByName(self.context, "portal_membership")
        if bool(tool.isAnonymousUser()):
            return 'must be authenticated to use atd'

        if 'data' in self.request.form:
            data = self.request.form
        else:
            data = self.request._file.read()

        service_url = settings.libraries_atd_service_url
        if not service_url.startswith('http'):
            service_url = 'https://' + service_url

        resp = requests.post(service_url + '/checkDocument', data=data)

        if resp.status_code != 200:
            raise Exception('Unexpected response code from AtD service %d' %
                            resp.status_code)

        self.request.RESPONSE.setHeader('content-type',
                                        'text/xml;charset=utf-8')
        respxml = resp.content
        xml = respxml.strip().replace("\r", '').replace("\n", '').replace(
            '>  ', '>')
        return xml
