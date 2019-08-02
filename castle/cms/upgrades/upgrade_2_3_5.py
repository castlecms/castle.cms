from Products.CMFCore.utils import getToolByName

import logging
log = logging.getLogger(__name__)

PROFILE_ID = 'profile-castle.cms:2_3_5'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
