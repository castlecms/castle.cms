from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from plone import api
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings

PROFILE_ID = 'profile-castle.cms:2_6_18'


def upgrade(site, logger=None):
    setup = getToolByName(site, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    registry = getUtility(IRegistry)
    try:
        whitelist_login_domains = api.portal.get_registry_record(name='whitelist_login_domains', default=None)
    except api.exc.InvalidParameterError:
        whitelist_login_domains = None

    if not whitelist_login_domains:
        whitelist_login_domains = field.List(title=u"Whitelist Login Domains",
                                             description=u"Allow users to login with email of these domains",
                                             value_type=field.TextLine(title=u"Value"))
        whitelist_login_domains = Record(whitelist_login_domains)
        registry._records['whitelist_login_domains'] = whitelist_login_domains

    cookWhenChangingSettings(site)
