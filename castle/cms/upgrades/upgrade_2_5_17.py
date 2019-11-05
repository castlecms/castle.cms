from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from castle.cms.cron._pw_expiry import update_password_expiry
from castle.cms.cron.utils import setup_site
from plone import api

def upgrade(context, logger=None):
    setup_site(context)
    auth_step_timeout = api.portal.get_registry_record('plone.auth_step_timeout', default=None)
    if not auth_step_timeout:
        api.portal.set_registry_record('plone.auth_step_timeout', 120)

    update_password_expiry(context)
