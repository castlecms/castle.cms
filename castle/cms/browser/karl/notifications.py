import logging
from plone import api
from zExceptions import Redirect
from Products.Five import BrowserView
from castle.cms.tasks import send_email

class RequestAccess():
    def __call__(self):
        try:
            group = 'test-group'
            roles = api.group.get_roles(groupname=group)
            if 'Site Administrator' not in roles:
                logging.error('specified group to send access requests do not have Site Administrator role', exc_info=True)
                raise Exception('specified group to send access requests do not have Site Administrator role')
            
            addresses = []
            for user in api.user.get_users(groupname=group):
                email = user.getProperty('email')
                if email:
                    addresses.append(email)
            
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
                sender='request_access_noreply@castlecms.com')
        except:
            self.request.response.setStatus(400)

class RequestForm(BrowserView):
    def info(self):
        pass
        
def groupNotification(obj, event):
    pass

def on_attachment_modify(obj, event):
    import pdb; pdb.set_trace()
    if event.new_state.id != 'published':
        groupNotification(obj, event)

def on_blog_modify(obj, event):
    import pdb; pdb.set_trace()
    if event.new_state.id != 'published':
        groupNotification(obj, event)

def on_page_modify(obj, event):
    import pdb; pdb.set_trace()
    if event.new_state.id != 'published':
        groupNotification(obj, event)

def on_attachment_publish(obj, event):
    import pdb; pdb.set_trace()
    state = api.content.get_state(obj=obj)
    if state != 'published':
        return
def on_blog_publish(obj, event):
    import pdb; pdb.set_trace()
    state = api.content.get_state(obj=obj)
    if state != 'published':
        return

def on_page_publish(obj, event):
    import pdb; pdb.set_trace()
    state = api.content.get_state(obj=obj)
    if state != 'published':
        return