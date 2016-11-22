from plone.tiles.interfaces import IPersistentTile
from zope.interface import Interface


class IGlobalTile(IPersistentTile):
    pass


class IMetaTile(IPersistentTile):
    pass


class IFieldTileRenderer(Interface):
    pass
