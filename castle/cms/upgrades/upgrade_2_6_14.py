from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings

PROFILE_ID = 'profile-castle.cms:2_6_14'


def upgrade(site, logger=None):
    setup = getToolByName(site, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(site)
