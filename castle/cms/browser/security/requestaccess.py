import logging

from plone import api
from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope.component import queryUtility
from zope.interface import implements

from castle.cms.browser.security.login import SecureLoginView
from castle.cms.interfaces import ISecureLoginAllowedView
from castle.cms.interfaces import IAuthenticator
from castle.cms.tasks import send_email


logger = logging.getLogger('Plone')


class RequestAccessView(BrowserView):
    implements(ISecureLoginAllowedView)

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

            system_email_address = registry.get('plone.system_email_address', None)
            configured_addresses = registry.get('plone.request_access_form_email_addresses', system_email_address)
            if configured_addresses is None:
                addresses = []
            else:
                addresses = list(set(configured_addresses.strip().splitlines()))

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
                self.request.response.redirect('{}/@@secure-login'.format(site_url))
                return

            logging.info("sending request access form submission to {}".format(", ".join(addresses)))
            send_email.delay(recipients=addresses, subject=subject, text=text)
            self.request.response.setStatus(302)
            self.request.response.redirect('{}/@@secure-login'.format(site_url))
        except Exception:
            logging.error("problem sending request access form", exc_info=True)
            self.request.response.setStatus(400)


    def request_info(self):
        registry = queryUtility(IRegistry)

        # we only send data that was requested to actually be sent to prevent exploitation
        # of the form as much as possible
        accepted_fields = registry.get('plone.request_access_form_accepted_fields', None)
        if accepted_fields is None:
            accepted_fields = []
        elif len(accepted_fields.strip()) <= 0:
            accepted_fields = []
        else:
            accepted_fields = accepted_fields.strip().splitlines()

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
