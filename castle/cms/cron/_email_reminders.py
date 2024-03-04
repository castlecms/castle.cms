from AccessControl.SecurityManagement import newSecurityManager
from DateTime import DateTime
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite
from castle.cms import cache
from castle.cms import utils
from copy import deepcopy

import logging


logger = logging.getLogger('castle.cms')


def send_reminders(site):
    setSite(site)

    cache_key = '-'.join(api.portal.get().getPhysicalPath()[1:]) + '-email-reminders'
    reminder_cache = {}

    try:
        reminder_cache = cache.get(cache_key)
    except KeyError:
        cache.set(cache_key, reminder_cache)
    portal_catalog = api.portal.get_tool('portal_catalog')

    for key, item in reminder_cache.items():
        results = portal_catalog.searchResults({'portal_type': item.get('portal_type'), 'id': item.get('pid')})
        for brain in results:
            obj = brain.getObject()
            roles = obj.get_local_roles_for_userid(item.get('uid'))
            obj_path = '/'.join(obj.getPhysicalPath())
            if 'Reviewer' in roles:
                if item.get('reminder_date') < DateTime():
                    try:
                        recipients=item['email']
                        subject="Page Assigned: %s" % (
                            api.portal.get_registry_record('plone.site_title'))
                        html="""
                            <p>Hi %s,</p>

                            <p>You have been assigned a new page:</p>
                            <p> %s </p>
                            <p>When your task is complete, you may un-assign yourself from this page.</p>""" % (
                                        item['name'], obj_path)
                        message = item.get('message')
                        if message:
                            html += """

                            <p> %s </p>
                            """ % (message)
                        
                        utils.send_email(
                            recipients=recipients,
                            subject=subject,
                            html=html
                        )
                    except Exception:
                        logger.warn('Could not send assignment email ', exc_info=True)
            else:
                new_cache = deepcopy(reminder_cache) # Not sure if deepcopy is necessary
                new_cache.pop(key, None)
                cache.set(cache_key, new_cache)
        
    


def run(app):
    singleton.SingleInstance('autopublish')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            try:
                send_reminders(obj)
            except Exception:
                logger.error('Could not update content for %s' % oid, exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa