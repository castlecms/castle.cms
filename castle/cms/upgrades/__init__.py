from castle.cms.interfaces import IAPISettings, ISecuritySchema
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
from Products.CMFCore.utils import getToolByName

import importlib
import plone.api as api


PROFILE_ID = 'profile-castle.cms:default'


def cook_js_resources(context, logger=None):
    cookWhenChangingSettings(api.portal.get())


def re_register_interface(interface, prefix):
    registry = api.portal.get_tool('portal_registry')
    registry.registerInterface(
        interface,
        prefix=prefix,
    )


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


def upgrade_3005(site, logger=None):
    # add in princexml username and password
    re_register_interface(IAPISettings, 'castle')


def upgrade_3006_cc(site, logger=None):
    # for explicit enable/disable of country code checking
    re_register_interface(ISecuritySchema, 'castle')


def upgrade_3006_ga4(site, logger=None):
    # for ga4 migration
    re_register_interface(IAPISettings, 'castle')
    old_ga_id = api.portal.get_registry_record('castle.google_analytics_id')
    if old_ga_id:
        api.portal.set_registry_record('castle.universal_analytics_id', old_ga_id)
        api.portal.set_registry_record('castle.google_analytics_id', u'')


upgrade_3007 = default_upgrade_factory('3007')


def upgrade_3008(site, logger=None):
    setup = getToolByName(site, 'portal_setup')
    full_profile_id = 'profile-castle.cms:{}'.format('3008')
    setup.runAllImportStepsFromProfile(full_profile_id)
    cookWhenChangingSettings(api.portal.get())
    re_register_interface(ISecuritySchema, 'castle')


upgrade_3009 = default_upgrade_factory('3009')
