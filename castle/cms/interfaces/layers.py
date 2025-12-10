from plone.app.contenttypes.interfaces import IPloneAppContenttypesLayer
from plone.app.mosaic.interfaces import IMosaicLayer
from plone.app.tiles.interfaces import ITilesFormLayer
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from wildcard.hps.interfaces import IWildcardHPSLayer


class ICastleLayer(
        IDefaultBrowserLayer,
        IMosaicLayer,
        ITilesFormLayer,
        IPloneAppContenttypesLayer,
        IWildcardHPSLayer):
    pass


class IVersionViewLayer(ICastleLayer):
    """
    when viewing a version of an object
    """
