from castle.cms import utils
from castle.cms.interfaces import ICastleLayer
from castle.cms.interfaces import IGlobalTile
from castle.cms.interfaces import IMetaTile
from castle.cms.interfaces import IVersionViewLayer
from plone.tiles.interfaces import ITile
from plone.tiles.interfaces import ITileDataContext
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import classImplements
from plone.tiles.interfaces import IPersistentTile
from plone.app.standardtiles.contentlisting import ContentListingTile


# make ContentListing persistent
classImplements(ContentListingTile, IPersistentTile)


@implementer(ITileDataContext)
@adapter(Interface, ICastleLayer, IGlobalTile)
def globalTileDataContext(context, request, tile):
    """
    Make sure to not pull from drafts data proxy
    """
    return tile.context


@implementer(ITileDataContext)
@adapter(Interface, ICastleLayer, IMetaTile)
def metaTileDataContext(context, request, tile):
    """
    Make sure to not pull from drafts data proxy
    """
    dc = getattr(tile, 'data_context', None)
    return dc or tile.context


@implementer(ITileDataContext)
@adapter(Interface, IVersionViewLayer, ITile)
def versionTileDataContext(context, request, tile):
    """
    Get version of context.
    This is used when viewing different versions of content
    """
    version = request.form.get('version')
    return utils.get_object_version(tile.context, version)
