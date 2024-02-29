from castle.cms import subscribe
from castle.cms import utils
from castle.cms.browser.utils import Utils
from collective.celery import task
from plone import api
from urllib import urlencode
from zope.globalrequest import getRequest
from castle.cms import cache
import logging


logger = logging.getLogger('castle.cms')


@task.as_admin()
def send_email(*args, **kwargs):
    utils.send_email(*args, **kwargs)


@task.as_admin()
def send_email_to_subscribers(subject, html, categories=None, sender=None):
    _utils = Utils(api.portal.get(), getRequest())
    public_url = _utils.get_public_url()

    check_categories = (categories is not None and len(categories) != 0)

    for subscriber in subscribe.all():
        if check_categories:
            # If there's no chosen categories, they recieve everything
            if ('categories' in subscriber and
                    len(subscriber['categories']) > 0):
                # make sure that this message falls under one of
                # their categories
                if len(categories.intersection(subscriber['categories'])) == 0:
                    continue

        query = urlencode({
            'email': subscriber.get('email'),
            'code': subscriber.get('code'),
        })

        unsubscribe_url = '%s/@@unsubscribe?%s' % (
            public_url.rstrip('/'),
            query)

        change_url = '%s/@@changesubscription?%s' % (
            public_url.rstrip('/'),
            query)

        unsubscribe_url = unsubscribe_url.encode('utf8')
        change_url = change_url.encode('utf8')

        html = html.replace('{{unsubscribe_url}}', unsubscribe_url)
        html = html.replace('{{change_url}}', change_url)

        utils.send_email([subscriber.get('email')], subject, html, sender=sender)


@task.as_admin()
def send_email_reminder(data=None):
    """
    This sends reminder emails to users who have been assigned to a page via the
    'Sharing' tab.
    The first email is sent upon initial assignment.
    The second is sent after five days if they haven't run-assigned themselves 
    from the page.
    """

    cache_key = '-'.join(api.portal.get().getPhysicalPath()[1:]) + '-email-reminders'
    notify_list = []

    try:
        notify_list = cache.get(cache_key)
    except KeyError:
        cache.set(cache_key, notify_list)

    
    if data:
        # A user has been assigned to a page
        # Their info will be added to the cache, and they will receive an email

        notify_list.append(data)
        cache.set(cache_key, notify_list)

        try:
            # TODO: Should the assigned roles be added to the email as well?
            utils.send_email(
                recipients=data.get('email'),
                subject="Page Assigned: %s" % (
                    api.portal.get_registry_record('plone.site_title')),
                html="""
                    <p>Hi %s,</p>

                    <p>You have been assigned a new page:</p>
                    <p> %s </p>
                    <p>When your task is complete, you may un-assign yourself from this page.</p>""" % (
                                data.get('name'), data.get('obj_path')))
        except Exception:
            logger.warn('Could not send page assignment email ', exc_info=True)
    
    else:
        # CRON run
        # print('=== actors ===')
        # actors = []
        # rt = api.portal.get_tool("portal_repository")
        # history = rt.getHistoryMetadata(self.context)
        # for i in range(history.getLength(countPurged=False)):
        #     data = history.retrieve(i, countPurged=False)
        #     actor = data["metadata"]["sys_metadata"]["principal"]
        #     actors.append(actor) if actor not in actors else None
        # print(actors)

        # print('=== contributors ===')
        # assigned_users = []

        # acl_users = api.portal.get_tool('acl_users')
        # local_roles = acl_users._getLocalRolesForDisplay(self.context)

        # for name, rolesm, rtype, rid in local_roles:
        #     print(name)
        #     print(rolesm)
        #     print(rtype)
        #     assigned_users.append(name)
        # print(assigned_users)
        pass
