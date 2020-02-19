from castle.cms.cron._pw_expiry import update_password_expiry
from plone.registry.interfaces import IRegistry
from plone.registry import field
from plone.registry import Record
from plone import api
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

PROFILE_ID = 'profile-castle.cms:2_5_18'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    # need to registry the dexterity type and slide type (profile)
    registry = getUtility(IRegistry)
