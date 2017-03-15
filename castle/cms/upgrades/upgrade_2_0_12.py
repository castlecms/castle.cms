from Products.CMFCore.utils import getToolByName


PROFILE_ID = 'profile-castle.cms.upgrades:2_0_12'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
