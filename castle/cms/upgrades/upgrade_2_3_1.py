from plone import api
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings


PROFILE_ID = 'profile-castle.cms.upgrades:2_3_1'

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
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(api.portal.get())

    setup.runImportStepFromProfile(
        'profile-collective.elasticsearch:default',
        'plone.app.registry',
        run_dependencies=False,
    )

    registry = getUtility(IRegistry)
    tiles = registry['castle.slot_tiles']
    for recover_type, recover_tiles in _recover_slot_tiles.items():
        if recover_type not in tiles:
            tiles[recover_type] = []
        for tile_id in recover_tiles:
            if tile_id not in tiles[recover_type]:
                tiles[recover_type].append(tile_id)
