from castle.cms.tasks import send_email
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry

class RequestAccess():
    def __call__(self):
        try:
            registry = queryUtility(IRegistry)
            addresses = registry.records['plone.system_email_addresses'].value
            sender = registry.records['plone.email_from_address'].value

            form = self.request.form
            subject = 'Request Access'
            text = '''
            Request Access
            --------------
            First Name: {}
            Last Name: {}
            Organization: {}
            Position: {}
            E-Mail: {}
            Phone Number: {}
            '''.format(form['fname'],
                       form['lname'],
                       form['org'],
                       form['position'],
                       form['email'],
                       form['phone'])
            send_email.delay(
                recipients=list(set(addresses)), 
                subject=subject, 
                text=text, 
                sender=sender)
        except:
            self.request.response.setStatus(400)
