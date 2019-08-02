from zope.component import getUtility
from plone.registry.interfaces import IRegistry


_recover_slot_tiles = {
    "Media": [
        "castle.cms.audiotile",
        "castle.cms.embedtile",
        "castle.cms.maptile",
        "castle.cms.gallerytile",
        "castle.cms.slidertile",
        "castle.cms.videotile",
        "castle.cms.imagetile"
    ],
    "Social": [
        "castle.cms.facebookPage",
        "castle.cms.pin",
        "castle.cms.twitterTimeline",
        "castle.cms.tweet",
        "castle.cms.sharing"
    ],
    "Advanced": [
        "castle.cms.fragment",
        "castle.cms.calendar",
        "castle.cms.survey",
        "castle.cms.querylisting",
        "plone.app.standardtiles.contentlisting",
        "castle.cms.navigation",
        "castle.cms.search"
    ]
}


def upgrade(context, logger=None):
    registry = getUtility(IRegistry)
    if registry['castle.slot_tiles'] is None:
        registry['castle.slot_tiles'] = {}
    tiles = registry['castle.slot_tiles']
    for recover_type, recover_tiles in _recover_slot_tiles.items():
        if recover_type not in tiles:
            tiles[recover_type] = []
        for tile_id in recover_tiles:
            if tile_id not in tiles[recover_type]:
                tiles[recover_type].append(tile_id)
