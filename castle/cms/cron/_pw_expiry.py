from tendo import singleton
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from plone import api
from .utils import setup_site
from castle.cms.pwexpiry.utils import days_since_event
from castle.cms.pwexpiry.utils import send_notification_email
from DateTime import DateTime
import time

import logging

# loop through acl users of each site, making sure they have the pwexpiry related
# data on them and send out expiration emails/warnings


logger = logging.getLogger('castle.cms')


def update_password_expiry(site):
    setup_site(site)

    pwexpiry_enabled = api.portal.get_registry_record('plone.pwexpiry_enabled', default=False)
    validity_period = api.portal.get_registry_record('plone.pwexpiry_validity_period', default=0)

    for user in api.user.get_users():
        if pwexpiry_enabled and validity_period > 0:
            whitelist = api.portal.get_registry_record('plone.pwexpiry_whitelisted_users', default=[])
            whitelisted = whitelist and user.getId() in whitelist
            if not whitelisted:
                password_date = user.getProperty('password_date', None)
                current_time = DateTime()

                if password_date:
                    since_last_pw_reset = days_since_event(
                        password_date.asdatetime(),
                        current_time.asdatetime()
                    )

                    remaining_days = validity_period - since_last_pw_reset
                    if remaining_days < 0:
                        # Password has expired
                        user.setMemberProperties({
                            'reset_password_required': True,
                            'reset_password_time': time.time()
                        })
                        continue
                    if remaining_days < 2:
                        send_notification_email(user, remaining_days)
                else:
                    user.setMemberProperties({
                        'password_date': current_time
                    })


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
