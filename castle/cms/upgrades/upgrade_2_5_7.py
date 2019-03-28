from Products.CMFCore.utils import getToolByName


PROFILE_ID = 'profile-castle.cms:2_5_7'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
