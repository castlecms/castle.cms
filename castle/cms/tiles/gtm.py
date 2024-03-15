from castle.cms.tiles.base import BaseTile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.interface import Interface


class GoogleTagManagerTile(BaseTile):

    def render(self):
        registry = getUtility(IRegistry)
        enabled = registry.get('castle.gtm_enabled', None)
        if enabled:
            return self.index()
        return ''

    @property
    def gtm_id(self):
        registry = getUtility(IRegistry)
        gtm_id = registry.get('castle.gtm_id', None)
        return gtm_id


class GoogleTagManagerTileSchema(Interface):
    pass


class GlobalSiteTagTile(BaseTile):

    def render(self):
        registry = getUtility(IRegistry)
        enabled = registry.get('castle.gst_enabled', None)
        if enabled:
            return self.index()
        return ''

    @property
    def gst_id(self):
        registry = getUtility(IRegistry)
        gst_id = registry.get('castle.gst_id', None)
        return gst_id


class GlobalSiteTagTileSchema(Interface):
    pass
