from AccessControl.SecurityManagement import newSecurityManager
from castle.cms.utils import retriable
from castle.cms.constants import TRASH_LOG_KEY
from DateTime import DateTime
from plone import api
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException
from plone.locking.interfaces import ILockable
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.annotation.interfaces import IAnnotations
from zope.component.hooks import setSite

import transaction
import logging


logger = logging.getLogger('castle.cms')


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
    deleted_count = 0
    not_deleted_count = 0
    empty_trash_log = 'The following items could not be deleted\n' \
                        'They may still be linked by other content.\n'
    for brain in catalog(**query):
        ob = brain.getObject()
        lockable = ILockable(ob, None)
        if lockable and lockable.locked():
            lockable.clear_locks()
        try:
            api.content.delete(ob)
            deleted_count += 1
        except LinkIntegrityNotificationException:
            not_deleted_count += 1
            logger.warn('Did not delete {} from trash, link integrity'.format(ob))
            empty_trash_log += '{}\n'.format(ob.absolute_url())
            pass
        if deleted_count % 20 == 0:
            transaction.commit()
    transaction.commit()
    site_annotations = IAnnotations(site)
    empty_trash_log += 'Deleted {} items, could not delete {} items'.format(
        deleted_count,
        not_deleted_count
    )
    site_annotations[TRASH_LOG_KEY] = empty_trash_log


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
