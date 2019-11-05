from tendo import singleton
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot

import logging

# loop through acl users of each site, making sure they have the pwexpiry related
# data on them and send out expiration emails/warnings


logger = logging.getLogger('castle.cms')


def update_password_expiry(site):
    pass


def run(app):
    singleton.SingleInstance('pwexpiry')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            try:
                update_password_expiry(obj)
            except Exception:
                logger.error('Could not update password expiry data for %s' % oid, exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa
