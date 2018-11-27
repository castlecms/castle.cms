from plone import api
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings


PROFILE_ID = 'profile-castle.cms.upgrades:2_1_0'


def upgrade(context, logger=None):
    # This value is being converted to a tuple, hold onto it or it will get
    # overwritten
    backend_url = api.portal.get_registry_record('plone.backend_url') or ''

    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(api.portal.get())

    if backend_url is not None:
        api.portal.set_registry_record('plone.backend_url', (backend_url,))
