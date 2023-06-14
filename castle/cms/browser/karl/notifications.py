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

def get_group(obj):
    groupname = '{}:members'.format(obj.__parent__.title)
    group = api.group.get(groupname=groupname)
    if obj.__parent__.title == "site":
        raise Exception('no group found')
    
    if group is not None:
        return groupname
    else:
        groupname = get_group(obj.__parent__)
    
    return groupname

def groupNotification(group, subject, text, mp):
    if mp == 'm':
        subject = 'Item modified: {}'.format(subject)
    elif mp == 'p':
        subject = 'New item published: {}'.format(subject)
    else:
        raise Exception('mp must be of value m for modified or p for published')
    
    addresses = []

    for user in api.user.get_users(groupname=group):
        email = user.getProperty('email')
        if email:
            addresses.append(email)
    send_email.delay(
        recipients='admin@foobar.com',  #list(set(addresses)), 
        subject=subject, 
        text=text, 
        sender='subscription_noreply@castlecms.com')

def on_attachment_modify(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj.title, obj.text, 'm')

def on_blog_modify(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj.title, obj.text, 'm')

def on_page_modify(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj.title, obj.text, 'm')

def on_attachment_publish(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj.title, obj.text, 'p')
    
def on_blog_publish(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj.title, obj.text, 'p')

def on_page_publish(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj.title, obj.text, 'p')