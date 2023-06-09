from plone import api
import requests
from zope import schema
from plone.app.contenttypes.interfaces import INewsItem
from zope.interface import implementer
from zope.component import adapter
from plone.dexterity.interfaces import IDexterityContent

class IPublish(INewsItem):

    published = schema.Bool(
        title=u'Publish',
        description=u'Check to publish content',
        required=True,
        default=False)

@implementer(IPublish)
@adapter(IDexterityContent)
class Publish(object):

    def __init__(self, context):
        self.context = context

def groupNotification(obj, event):
    import pdb; pdb.set_trace()
    sender = 'noreply@wildcardcorp.com'

    subject = 'test'
    message = 'testing to see if this works'

    api.portal.send_email(
        recipient='katie.wiessfelt@wildcardcorp.com',
        sender=sender,
        subject=subject,
        body=message,
    )

def on_attachment_modify(obj, event):
    import pdb; pdb.set_trace()
    if event.new_state.id != 'published':
        groupNotification(obj, event)

def on_blog_modify(obj, event):
    import pdb; pdb.set_trace()
    if event.new_state.id != 'published':
        groupNotification(obj, event)

def on_file_modify(obj, event):
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

def on_file_publish(obj, event):
    import pdb; pdb.set_trace()
    state = api.content.get_state(obj=obj)
    if state != 'published':
        return
    
    # matching_users = acl_users.searchUsers(fullname=presenter.title)
    # for user_info in matching_users:
    #     email = user_info.get('email', None)
    #     if email is not None:
    #         api.portal.send_email(
    #             recipient=email,
    #             sender=sender,
    #             subject=subject,
    #             body=message,
    #         )