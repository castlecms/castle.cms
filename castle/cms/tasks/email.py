from castle.cms import subscribe
from castle.cms import utils
from castle.cms.browser.utils import Utils
from collective.celery import task
from plone import api
from urllib import urlencode
from zope.globalrequest import getRequest
from castle.cms import cache
from DateTime import DateTime
from copy import deepcopy
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
def send_email_reminder(obj=None, data=None):
    """
    This sends reminder emails to users who have been assigned to a page via the
    'Sharing' tab.
    The first email is sent upon initial assignment.
    The second is sent after five days if they haven't un-assigned themselves 
    from the page.
    """

    cache_key = '-'.join(api.portal.get().getPhysicalPath()[1:]) + '-email-reminders'
    reminder_cache = {}

    try:
        reminder_cache = cache.get(cache_key)
    except KeyError:
        cache.set(cache_key, reminder_cache)

    if obj:
        # A user has been assigned to a page
        item_key = obj.getId() + '#' + data['uid']
        if item_key not in reminder_cache:

            data['pid'] = obj.getId()
            data['portal_type'] = obj.portal_type
            data['reminder_date'] = DateTime() + 5

            # Set key as page id + user id so each user/page association can be tracked individually
            reminder_cache[data['pid'] + '#' + data['uid']] = data
            cache.set(cache_key, reminder_cache)

            obj_path = obj.getPhysicalPath()

            try:
                utils.send_email(
                    recipients=data['email'],
                    subject="Page Assigned: %s" % (
                        api.portal.get_registry_record('plone.site_title')),
                    html="""
                        <p>Hi %s,</p>

                        <p>You have been assigned a new page:</p>
                        <p> %s </p>
                        <p>When your task is complete, you may un-assign yourself from this page.</p>""" % (
                                    data['name'], obj_path))
            except Exception:
                logger.warn('Could not send assignment email ', exc_info=True)
        else:
            # Assignment exists in cache
            if 'Reviewer' not in data['roles']:
                new_cache = deepcopy(reminder_cache) # Not sure if deepcopy is necessary
                new_cache.pop(item_key, None)
                cache.set(cache_key, new_cache)

    else:
        # CRON run
        portal_catalog = api.portal.get_tool('portal_catalog')

        for key, item in reminder_cache.items():
            results = portal_catalog.searchResults({'portal_type': item.get('portal_type'), 'id': item.get('pid')})
            for brain in results:
                obj = brain.getObject()
                roles = obj.get_local_roles_for_userid(item.get('uid'))
                if 'Reviewer' in roles:
                    if item.get('reminder_date') < DateTime():
                        try:
                            utils.send_email(
                                recipients=data['email'],
                                subject="Page Assigned: %s" % (
                                    api.portal.get_registry_record('plone.site_title')),
                                html="""
                                    <p>Hi %s,</p>

                                    <p>You have been assigned a new page:</p>
                                    <p> %s </p>
                                    <p>When your task is complete, you may un-assign yourself from this page.</p>""" % (
                                                data['name'], obj_path))
                        except Exception:
                            logger.warn('Could not send assignment email ', exc_info=True)
                else:
                    new_cache = deepcopy(reminder_cache) # Not sure if deepcopy is necessary
                    new_cache.pop(key, None)
                    cache.set(cache_key, new_cache)
