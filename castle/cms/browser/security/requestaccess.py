from castle.cms.tasks import send_email
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry

class RequestAccess():
    
    def __call__(self):
        try:
            registry = queryUtility(IRegistry)
            addresses = registry.records['plone.system_email_addresses'].value
            sender = registry.records['plone.email_from_address'].value
            self.registry = registry
            fields = self.fields()

            subject = 'Request Access'
            text = 'Request Access\n--------------\n{}'.format(fields)
            send_email.delay(
                recipients=list(set(addresses)), 
                subject=subject, 
                text=text, 
                sender=sender)
        except:
            self.request.response.setStatus(400)
    
    def fields(self):
        form = self.request.form
        fields_str = self.registry.records['plone.form_fields'].value
        fields = fields_str.split(',')
        return_str = ''
        for field in fields:
            title = field.strip()
            name = field.strip().lower()
            return_str += '{}: {}\n'.format(title, form[name])
        return return_str
        

class RequestForm():
    def fields(self):
        registry = queryUtility(IRegistry)
        fields_str = registry.records['plone.form_fields'].value
        fields = fields_str.split(',')
        for field in fields:
            index = fields.index(field)
            fields[index] = field.strip()
        return fields