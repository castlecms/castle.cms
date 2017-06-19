from plone import api
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
from castle.cms import utils
#from zope.component import getGlobalSiteManager
#from castle.cms.indexers import recurrence
import logging
log = logging.getLogger(__name__)

PROFILE_ID = 'profile-castle.cms.upgrades:2_0_34'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    # Reindex events that have recurrences
    brains = api.content.find(portal_type='Event')
    for brain in brains:
        obj = brain.getObject() # unfortunate but necessary
        if hasattr(obj, 'recurrence') and obj.recurrence is not None:
            log.info('reindexing recurrence of %s' % brain.Title)
            brain.getObject().reindexObject(idxs=['recurrence'])
    cookWhenChangingSettings(api.portal.get())
