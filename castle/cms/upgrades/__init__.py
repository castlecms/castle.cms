from castle.cms.interfaces import (
    IAPISettings,
    ISecuritySchema,
)
from importlib import import_module
from logging import getLogger
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
from Products.CMFCore.utils import getToolByName
from zope.interface import noLongerProvides

import plone.api as api


CASTLE_LOGGER = getLogger('castle.cms')
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
    upgrade_file = import_module('castle.cms.upgrades.upgrade_' + profile_id)
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


def upgrade_3011(site, logger=CASTLE_LOGGER):
    try:
        # this interface can be completely removed once we verify no content objects provide it
        # we don't want this upgrade step to break once ITemplate is gone, so import this way
        from castle.cms.interfaces import ITemplate

        portal_types_tool = api.portal.get_tool('portal_types')
        itemplate_objects = []

        # reindex site so we can be sure we really find every object that provides ITemplate
        # since we're already iterating through every object on the site, collect the objects
        # we care about in this step instead of a catalog search
        for portal_type in portal_types_tool:
            logger.info('reindexing object_provides for portal_type ' + portal_type)
            # this could take a while
            for portal_type_brain in api.content.find(portal_type=portal_type):
                try:
                    content_object = portal_type_brain.getObject()
                    content_object.reindexObject(idxs=['object_provides'])
                    if ITemplate.providedBy(content_object):
                        itemplate_objects.append(content_object)
                except Exception:
                    logger.info('something weird happened with ' + repr(portal_type_brain))
                    continue

        itemplate_object_count = len(itemplate_objects)
        plural_suffix = '' if itemplate_object_count == 1 else 's'
        logger.info('{itemplate_object_count} content object{plural_suffix} provided ITemplate interface'.format(
            itemplate_object_count=itemplate_object_count,
            plural_suffix=plural_suffix,
        ))

        for itemplate_object in itemplate_objects:
            logger.info('removing ITemplate from object ' + itemplate_object.id)
            noLongerProvides(itemplate_object, ITemplate)
            itemplate_object.reindexObject(idxs=['object_provides'])
    except ImportError:
        logger.info('ITemplate no longer exists, skipping most of this upgrade step')

    try:
        del api.portal.get().template_list
        logger.info('Deleted "template_list" from Portal object')
    except AttributeError:
        logger.info('Portal object did not have property "template_list"')


upgrade_3012 = default_upgrade_factory('3012')
upgrade_3013 = default_upgrade_factory('3013')
