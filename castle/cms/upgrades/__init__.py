from plone.api import portal
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
from Products.CMFCore.utils import getToolByName

import importlib


PROFILE_ID = 'profile-castle.cms:default'


def cook_js_resources(context, logger=None):
    cookWhenChangingSettings(portal.get())


def custom_upgrade_factory(profile_id):
    upgrade_file = importlib.import_module('castle.cms.upgrades.upgrade_' + profile_id)
    return upgrade_file.upgrade


def default_upgrade_factory(profile_id):
    def upgrade_function(site, logger=None):
        setup = getToolByName(site, 'portal_setup')
        full_profile_id = 'profile-castle.cms:{}'.format(profile_id)
        setup.runAllImportStepsFromProfile(full_profile_id)
        cookWhenChangingSettings(portal.get())
    return upgrade_function


def profileless_upgrade_factory():
    def upgrade(context, logger=None):
        cookWhenChangingSettings(portal.get())
    return upgrade


upgrade_2_0_12 = default_upgrade_factory('2_0_12')
upgrade_2_0_16 = default_upgrade_factory('2_0_16')
upgrade_2_0_41 = default_upgrade_factory('2_0_41')

upgrade_2_1_0 = custom_upgrade_factory('2_1_0')
upgrade_2_1_1 = custom_upgrade_factory('2_1_1')

upgrade_2_2_0 = custom_upgrade_factory('2_2_0')

upgrade_2_3_0 = default_upgrade_factory('2_3_0')
upgrade_2_3_1 = custom_upgrade_factory('2_3_1')
upgrade_2_3_2 = custom_upgrade_factory('2_3_2')
upgrade_2_3_3 = custom_upgrade_factory('2_3_3')
upgrade_2_3_5 = default_upgrade_factory('2_3_5')
upgrade_2_3_7 = profileless_upgrade_factory()
upgrade_2_3_8 = default_upgrade_factory('2_3_8')

upgrade_2_4_0 = profileless_upgrade_factory()

upgrade_2_5_0 = default_upgrade_factory('2_5_0')
upgrade_2_5_5 = default_upgrade_factory('2_5_5')
upgrade_2_5_7 = default_upgrade_factory('2_5_7')
upgrade_2_5_15 = default_upgrade_factory('2_5_15')
upgrade_2_5_17 = custom_upgrade_factory('2_5_17')
upgrade_2_5_19 = default_upgrade_factory('2_5_19')

upgrade_2_6_2 = default_upgrade_factory('2_6_2')
upgrade_2_6_11 = custom_upgrade_factory('2_6_11')
upgrade_2_6_12 = default_upgrade_factory('2_6_12')
upgrade_2_6_14 = default_upgrade_factory('2_6_14')
upgrade_2_6_16 = default_upgrade_factory('2_6_16')
upgrade_2_6_23 = default_upgrade_factory('2_6_23')
upgrade_2_6_25 = default_upgrade_factory('2_6_25')
upgrade_2_6_27 = default_upgrade_factory('2_6_27')
upgrade_2_6_30 = default_upgrade_factory('2_6_30')
upgrade_2_6_31 = default_upgrade_factory('2_6_31')
