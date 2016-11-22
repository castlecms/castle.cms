from AccessControl.SecurityManagement import newSecurityManager
from castle.cms.utils import retriable
from DateTime import DateTime
from plone import api
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException
from plone.locking.interfaces import ILockable
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite

import transaction


@retriable(sync=True)
def empty(site):
    setSite(site)
    catalog = api.portal.get_tool('portal_catalog')
    end = DateTime() - 30
    query = dict(
        modified={
            'query': (DateTime('1999/09/09'), end),
            'range': 'min:max'
        },
        trashed=True)
    count = 0
    for brain in catalog(**query):
        count += 1
        ob = brain.getObject()
        lockable = ILockable(ob, None)
        if lockable and lockable.locked():
            lockable.clear_locks()
        try:
            api.content.delete(ob)
        except LinkIntegrityNotificationException:
            # quietly ignore for now
            pass
        if count % 20 == 0:
            transaction.commit()
    transaction.commit()


def run(app):
    singleton.SingleInstance('emptytrash')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            empty(obj)


if __name__ == '__main__':
    run(app)  # noqa
