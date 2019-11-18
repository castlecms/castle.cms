from castle.cms.cron._pw_expiry import update_password_expiry
from plone import api


def upgrade(context, logger=None):
    auth_step_timeout = api.portal.get_registry_record(name='plone.auth_step_timeout', default=None)
    if not auth_step_timeout:
        api.portal.set_registry_record(name='plone.auth_step_timeout', value=120)

    update_password_expiry(api.portal.get())
