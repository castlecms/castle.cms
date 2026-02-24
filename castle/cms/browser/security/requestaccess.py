from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.interface import implementer

from castle.cms.browser.security.login import SecureLoginView
from castle.cms.interfaces import ISecureLoginAllowedView
from castle.cms.interfaces import IAuthenticator
from castle.cms.tasks import send_email

import logging
import plone.api as api

logger = logging.getLogger('Plone')


@implementer(ISecureLoginAllowedView)
class RequestAccessView(BrowserView):

    default_fields = ['name', 'email', 'phone']

    @property
    def accepted_fields(self):
        fields_string = api.portal.get_registry_record(
            'plone.request_access_form_accepted_fields',
            default='',
        )
        fields = [
            field.strip()
            for field in fields_string.splitlines()
            if len(field.strip()) > 0
        ]
        if len(fields) == 0:
            return self.default_fields
        return fields

    @property
    def request_access_email_addresses(self):
        if api.portal.get_registry_record('plone.request_access_enabled', default=False) is False:
            return []
        system_email_address = api.portal.get_registry_record('plone.system_email_address', default='')
        access_request_email_addresses = api.portal.get_registry_record(
            'plone.request_access_form_email_addresses',
            default=system_email_address,
        )
        return list(set([
            email.strip()
            for email in access_request_email_addresses.splitlines()
            if len(email.strip()) > 0
        ]))

    @property
    def request_access_enabled(self):
        if api.portal.get_registry_record('plone.request_access_enabled', default=False) is False:
            return False
        if len(self.request_access_email_addresses) == 0:
            return False
        return True

    def __init__(self, context, request):
        super(RequestAccessView, self).__init__(context, request)
        self.auth = self.authenticator = getMultiAdapter((context, request), IAuthenticator)

    def __call__(self):
        if self.request.REQUEST_METHOD == 'POST':
            self.request.response.setHeader('Content-type', 'application/json')
            return self.request_access()
        else:
            return self.index()

    def request_access(self):
        try:
            registry = queryUtility(IRegistry)

            site_title = registry.get('plone.site_title', 'CastleCMS')
            site_url = api.portal.get().absolute_url()

            addresses = self.request_access_email_addresses
            fields = self.request_info()
            subject = 'Request Access Form Submission on {}'.format(site_title)
            text = 'Request Access Form Data\n--------------\n{}'.format(fields)

            # no need to send anything if no recipient addresses can be determined
            if len(addresses) <= 0:
                logging.info(
                    "system address and request access form email addresses not configured, "
                    "not sending any request access form submission:"
                    "\n\nSubject: {}\n\n{}\n\n".format(subject, text))
                self.request.response.setStatus(302)
                self.request.response.redirect('{}/@@secure-login?submit=false'.format(site_url))
                return

            logging.info("sending request access form submission to {}".format(", ".join(addresses)))
            send_email.delay(recipients=addresses, subject=subject, text=text)
            self.request.response.setStatus(302)
            self.request.response.redirect('{}/@@secure-login?submit=true'.format(site_url))
        except Exception:
            logging.error("problem sending request access form", exc_info=True)
            self.request.response.setStatus(400)

    def request_info(self):
        # we only send data that was requested to actually be sent to prevent exploitation
        # of the form as much as possible
        accepted_fields = self.accepted_fields

        form = self.request.form
        values = []
        for field in form.keys():
            if field.strip() not in accepted_fields:
                continue
            values.append("{}: {}".format(field, form[field]))

        return "\n".join(values)

    def scrub_backend(self):
        secure = SecureLoginView(self.context, self.request)
        return secure.scrub_backend()
