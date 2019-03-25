from plone import api
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings


PROFILE_ID = 'profile-castle.cms:2_5_5'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(api.portal.get())
