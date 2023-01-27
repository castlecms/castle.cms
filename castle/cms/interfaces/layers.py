# IElasticSearchLayer ensures that if collective.elasticsearch is installed
# as an addon in a site, that the "search" view is overridden correctly by castle.cms
# this should be considered deprecated behavior, and will be removed in a
# future release.
from collective.elasticsearch.interfaces import IElasticSearchLayer

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
        IElasticSearchLayer,  # included to ensure compatibility, see note by import
        IWildcardHPSLayer):
    pass


class IVersionViewLayer(ICastleLayer):
    """
    when viewing a version of an object
    """
