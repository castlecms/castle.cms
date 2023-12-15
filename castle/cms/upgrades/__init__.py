from castle.cms.interfaces import IAPISettings, ISecuritySchema
from castle.cms.browser.controlpanel.openai import IOpenAISettings
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
from Products.CMFCore.utils import getToolByName

import importlib
import plone.api as api

from castle.cms.tiles.dynamic import get_tile_manager
from plone.app.mosaic.registry import MosaicRegistry


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
    re_register_interface(ISecuritySchema, 'plone')


def upgrade_3006_ga4(site, logger=None):
    # for ga4 migration
    re_register_interface(IAPISettings, 'castle')
    old_ga_id = api.portal.get_registry_record('castle.google_analytics_id')
    if old_ga_id:
        api.portal.set_registry_record('castle.universal_analytics_id', old_ga_id)
        api.portal.set_registry_record('castle.google_analytics_id', u'')


upgrade_3007 = default_upgrade_factory('3007')


def upgrade_3008(site, logger=None):
    re_register_interface(ISecuritySchema, 'plone')
    registry_records = api.portal.get_tool('portal_registry').records
    for security_schema_field_name in ISecuritySchema.names():
        try:
            del registry_records['castle.' + security_schema_field_name]
        except KeyError:
            # record not found
            pass


upgrade_3009 = default_upgrade_factory('3009')
upgrade_3010 = default_upgrade_factory('3010')

def upgrade_3011_interface_registry(setup_tool, logger=None):
    registry = api.portal.get_tool('portal_registry')
    registry.registerInterface(
        IOpenAISettings,
        prefix='castle',
    )
def upgrade_3011_register_profile(setup_tool, logger=None):
    # registry = api.portal.get_tool('portal_registry')
    # reg = MosaicRegistry(registry)
    # result = reg.parseRegistry
    # mng = get_tile_manager()
    # for tile in mng.get_tiles():
    #     if tile.get('hidden'):
    #         continue
    #     key = 'castle_cms_dynamic_{}'.format(tile['id'])
    #     category = tile.get('category') or 'advanced'
    #     category_id = category.replace(' ', '_').lower()
    #     if category_id not in result['plone']['app']['mosaic']['tiles_categories']:
    #         result['plone']['app']['mosaic']['tiles_categories'][category_id] = {
    #             'label': category,
    #             'name': category_id,
    #             'weight': 100
    #             }
    #         result['plone']['app']['mosaic']['app_tiles'][key] = {
    #             'category': category_id,
    #             'default_value': None,
    #             'favorite': False,
    #             'label': tile['title'],
    #             'name': tile['name'],
    #             'tile_type_id': u'castle.cms.dynamic',
    #             'read_only': False,
    #             'rich_text': False,
    #             'settings': True,
    #             'tile_type': u'app',
    #             'weight': tile['weight']
    #         }
    # import pdb; pdb.set_trace()
    default_upgrade_factory('3011')
