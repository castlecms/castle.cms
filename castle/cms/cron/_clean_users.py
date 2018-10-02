from AccessControl.SecurityManagement import newSecurityManager
from castle.cms.utils import retriable
from datetime import datetime
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.component.hooks import setSite

import logging
import transaction


logger = logging.getLogger('castle.cms')


@retriable(sync=True)
def delete_user(user):
    # need to clean/change ownership of content
    admin_user = api.user.get('admin')
    if admin_user:
        admin_user = admin_user.getUser()
        catalog = api.portal.get_tool('portal_catalog')
        for brain in catalog(Creator=user.getId()):
            ob = brain.getObject()
            ob.changeOwnership(admin_user, recursive=False)
            ob.reindexObjectSecurity()

    site = getSite()
    acl_users = site.acl_users
    if not user.canDelete():
        return
    try:
        acl_users.user_folderDelUsers([user.getId()])
    except (AttributeError, NotImplementedError):
        pass

    # Delete member data in portal_memberdata.
    mdtool = getToolByName(site, 'portal_memberdata', None)
    mtool = getToolByName(site, 'portal_membership')
    if mdtool is not None:
        mdtool.deleteMemberData(user.getId())

    # Delete members' local roles.
    mtool.deleteLocalRoles(site, [user.getId()], reindex=1, recursive=1)


def clean(site):
    setSite(site)
    registry = getUtility(IRegistry)
    days_to_clean_disabled_users = registry.get(
        'plone.days_to_clean_disabled_users', 30)
    for user in api.user.get_users():
        if api.user.get_roles(user=user) == ['Authenticated']:
            # compare when user was last modified
            diff = datetime.utcnow() - datetime.fromtimestamp(user._p_mtime)
            minutes = diff.seconds / 60
            hours = minutes / 60
            days = hours / 24
            if days >= days_to_clean_disabled_users:
                delete_user(user)
    transaction.commit()


def run(app):
    singleton.SingleInstance('cleanusers')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            try:
                clean(obj)
            except Exception:
                logger.error('Could not clean users %s' % oid, exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa
