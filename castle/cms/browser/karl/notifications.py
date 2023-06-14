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

def groupNotification(group, obj, mp):
    item = obj.portal_type
    if item == 'News Item':
        _type = 'Blog Entry'
    if item == 'Document':
        _type = 'Page'
    if item == 'Audio' or item == 'Media' or item == 'File':
        _type = 'Attachment'
    if mp == 'm':
        subject = '{} modified: {}'.format(_type, obj.title)
    elif mp == 'p':
        subject = 'New {} published: {}'.format(_type, obj.title)
    else:
        raise Exception('mp must be of value m for modified or p for published')
    
    contributors = ''
    for person in obj.contributors:
        contributors += '{}, '.format(person)
    contributors = contributors[:-2]

    addresses = []
    try:
        text = obj.text.raw.encode('utf-8')
    except:
        text = '<p>{}</p>'.format(obj.text)
    if text is unicode:
        try:
            text.encode('ascii')
        except:
            text.encode('utf-8')
    for user in api.user.get_users(groupname=group):
        email = user.getProperty('email')
        if email:
            addresses.append(email)
    html = """
        <h2>{}</h2>
        <h5>Contributors: {}</h5>
        {}

        <a href="{}">Click here to view on site</a>
    """.format(subject,
               contributors,
               text,
               obj.absolute_url())
    send_email.delay(
        recipients=list(set(addresses)), 
        subject=subject, 
        html=html, 
        sender='subscription_noreply@castlecms.com')

def on_attachment_modify(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj, 'm')

def on_blog_modify(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj, 'm')

def on_page_modify(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj, 'm')

def on_attachment_publish(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj, 'p')
    
def on_blog_publish(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj, 'p')

def on_page_publish(obj, event):
    group = get_group(obj)
    state = api.content.get_state(obj=obj)
    if state == 'published':
        groupNotification(group, obj, 'p')