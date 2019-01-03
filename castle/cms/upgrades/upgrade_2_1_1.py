from plone import api
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings


PROFILE_ID = 'profile-castle.cms:2_1_1'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile('profile-Products.PloneKeywordManager:default')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(api.portal.get())
