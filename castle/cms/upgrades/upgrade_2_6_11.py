from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings

PROFILE_ID = 'profile-castle.cms:2_6_11'


def upgrade(site, logger=None):
    setup = getToolByName(site, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(site)
    recursive_index(site)


def recursive_index(obj):
    if not IPloneSiteRoot.providedBy(obj):
        obj.reindexObject(idxs=['self_or_child_has_title_description_and_image'])
    for childID in obj.objectIds():
        recursive_index(obj[childID])
