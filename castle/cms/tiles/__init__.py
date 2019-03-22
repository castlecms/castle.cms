from castle.cms import utils
from castle.cms.interfaces import ICastleLayer
from castle.cms.interfaces import IGlobalTile
from castle.cms.interfaces import IMetaTile
from castle.cms.interfaces import IVersionViewLayer
from plone import api
from plone.app.standardtiles.contentlisting import ContentListingTile
from plone.app.standardtiles.raw import HTMLTile
from plone.resource.interfaces import IResourceDirectory
from plone.tiles.data import defaultPersistentTileDataStorage
from plone.tiles.interfaces import IPersistentTile
from plone.tiles.interfaces import ITile
from plone.tiles.interfaces import ITileDataContext
from plone.tiles.interfaces import ITileDataStorage
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.interface import Interface
from zope.interface import classImplements
from zope.interface import implementer


# make ContentListing and HTML persistent
classImplements(ContentListingTile, IPersistentTile)
classImplements(HTMLTile, IPersistentTile)


@implementer(ITileDataContext)
@adapter(Interface, ICastleLayer, IGlobalTile)
def GlobalTileDataContext(context, request, tile):
    """
    Make sure to not pull from drafts data proxy
    """
    return tile.context


@implementer(ITileDataContext)
@adapter(Interface, ICastleLayer, IMetaTile)
def MetaTileDataContext(context, request, tile):
    """
    Make sure to not pull from drafts data proxy
    """
    dc = getattr(tile, 'data_context', None)
    return dc or tile.context


@implementer(ITileDataContext)
@adapter(Interface, IVersionViewLayer, ITile)
def VersionTileDataContext(context, request, tile):
    """
    Get version of context.
    This is used when viewing different versions of content
    """
    version = request.form.get('version')
    return utils.get_object_version(tile.context, version)


@implementer(IAnnotations)
@adapter(IResourceDirectory)
def ResourceDirectoryAnnotations(context):
    # resource directory does not and should not implement annotation
    # storage. We should just proxy to the annotations on the site here
    # This fixes some errors when previewing the theme from the layout editor
    return IAnnotations(api.portal.get())


@implementer(ITileDataStorage)
@adapter(Interface, ICastleLayer, ITile)
def TileDataStorage(context, request, tile):
    if (tile.request.get('X-Tile-Persistent') or
            getattr(request, 'tile_persistent', False) or
            IPersistentTile.providedBy(tile)):
        return defaultPersistentTileDataStorage(context, request, tile)
    else:
        return IAnnotations(tile.request, tile.request.form)
