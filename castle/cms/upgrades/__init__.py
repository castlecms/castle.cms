from castle.cms.interfaces import IAPISettings
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
from Products.CMFCore.utils import getToolByName

import importlib
import plone.api as api


PROFILE_ID = 'profile-castle.cms:default'


def cook_js_resources(context, logger=None):
    cookWhenChangingSettings(api.portal.get())


def custom_upgrade_factory(profile_id):
    upgrade_file = importlib.import_module('castle.cms.upgrades.upgrade_' + profile_id)
    return upgrade_file.upgrade


def default_upgrade_factory(profile_id):
    def upgrade_function(site, logger=None):
        setup = getToolByName(site, 'portal_setup')
        full_profile_id = 'profile-castle.cms:{}'.format(profile_id)
        setup.runAllImportStepsFromProfile(full_profile_id)
        cookWhenChangingSettings(api.portal.get())
    return upgrade_function


def profileless_upgrade_factory():
    def upgrade(context, logger=None):
        cookWhenChangingSettings(api.portal.get())
    return upgrade


upgrade_3000 = default_upgrade_factory('3000')
upgrade_3001 = default_upgrade_factory('3001')
upgrade_3003 = default_upgrade_factory('3003')
upgrade_3004 = default_upgrade_factory('3004')
upgrade_3006 = default_upgrade_factory('3006')


def upgrade_3005(site, logger=None):
    registry = api.portal.get_tool('portal_registry')
    registry.registerInterface(
        IAPISettings,
        prefix='castle',
    )
