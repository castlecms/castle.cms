from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings

PROFILE_ID = 'profile-castle.cms:2_6_6'


def upgrade(site, logger=None):
    setup = getToolByName(site, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(site)

    for id in site.objectIds():
        site[id].reindexObject(['has_title_description_and_image'])
