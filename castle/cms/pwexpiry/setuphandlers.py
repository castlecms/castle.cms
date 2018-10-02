# -*- coding: utf-8 -*-
try:
    from Products.CMFPlone import __version__ as plone_version
except ImportError:
    plone_version = '4'

import logging

from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.Extensions.Install import activatePluginInterfaces
from Products.PluggableAuthService.interfaces.plugins import IChallengePlugin
from pwexpiry_plugin import addPwExpiryPlugin

logger = logging.getLogger('castle.cms.pwexpiry')


def import_various(context):
    """
    Install the PwExpiryPlugin
    """
    portal = context.getSite()

    acl = getToolByName(portal, 'acl_users')
    installed = acl.objectIds()

    if 'pwexpiry' not in installed:
        addPwExpiryPlugin(acl, 'pwexpiry', 'PwExpiry Plugin')
        activatePluginInterfaces(portal, 'pwexpiry')
        for i in range(len(acl.plugins.listPluginIds(IChallengePlugin))):
            acl.plugins.movePluginsUp(IChallengePlugin, ['pwexpiry'])
    else:
        logger.info('pwexpiry already installed')
