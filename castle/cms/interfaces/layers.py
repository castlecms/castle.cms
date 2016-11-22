from collective.elasticsearch.interfaces import IElasticSearchLayer
from plone.app.contenttypes.interfaces import IPloneAppContenttypesLayer
from plone.app.mosaic.interfaces import IMosaicLayer
from plone.app.tiles.interfaces import ITilesFormLayer
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICastleLayer(IDefaultBrowserLayer, IMosaicLayer, ITilesFormLayer,
                   IPloneAppContenttypesLayer, IElasticSearchLayer):
    pass


class IVersionViewLayer(ICastleLayer):
    """
    when viewing a version of an object
    """
