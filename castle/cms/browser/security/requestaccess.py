from castle.cms.tasks import send_email
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry
from zope.interface import implements
from Products.Five import BrowserView
from castle.cms.interfaces import ISecureLoginAllowedView
from castle.cms.interfaces import IAuthenticator
from zope.component import getMultiAdapter
from .login import SecureLoginView

class RequestAccessView(BrowserView):
    implements(ISecureLoginAllowedView)

    def __init__(self, context, request):
        super(RequestAccessView, self).__init__(context, request)
        self.auth = self.authenticator = getMultiAdapter(
            (context, request), IAuthenticator)
    def __call__(self):
        if self.request.REQUEST_METHOD == 'POST':
            self.request.response.setHeader('Content-type', 'application/json')
            return self.request_access()
        else:
            return self.index()
    def request_access(self):
        try:
            registry = queryUtility(IRegistry)
            self.registry = registry
            
            addresses = registry.records['plone.system_email_addresses'].value
            sender = registry.records['plone.email_from_address'].value
            
            fields = self.request_info()

            subject = 'Request Access'
            text = 'Request Access\n--------------\n{}'.format(fields)
            send_email.delay(
                recipients=list(set(addresses)), 
                subject=subject, 
                text=text, 
                sender=sender)
            self.request.response.setStatus(302)
            parents = self.request.get('PARENTS')
            for parent in parents:
                if parent.title == 'site':
                    url = parent.tpURL()
            self.request.response.redirect('{}/@@secure-login'.format(url))
        except:
            self.request.response.setStatus(400)
    
    def request_info(self):
        form = self.request.form
        fields_str = self.registry.records['plone.form_fields'].value
        fields = fields_str.split(',')
        return_str = ''
        for field in fields:
            title = field.strip()
            name = field.strip().lower()
            return_str += '{}: {}\n'.format(title, form[name])
        return return_str
    
    def fields(self):
        registry = queryUtility(IRegistry)
        fields_str = registry.records['plone.form_fields'].value
        fields = fields_str.split(',')
        for field in fields:
            index = fields.index(field)
            fields[index] = field.strip()
        return fields
    
    def scrub_backend(self):
        secure = SecureLoginView(self.context, self.request)
        return secure.scrub_backend()