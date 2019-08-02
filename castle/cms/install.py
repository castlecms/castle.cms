from castle.cms.exportimport.frontpagecontent import getTileData
from castle.cms.interfaces import ICastleLayer
from castle.cms.interfaces import IGlobalTile
from castle.cms.tiles.meta import MetaTile
from DateTime import DateTime
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.tiles.interfaces import IPersistentTile
from plone.tiles.interfaces import ITileDataManager
from Products.CMFPlone.interfaces import INonInstallable
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implements


class HiddenProducts(object):
    implements(INonInstallable)

    def getNonInstallableProducts(self):
        return []

    def getNonInstallableProfiles(self):
        return [
            'plone.formwidget.querystring:default',
            'plone.session:default',
            'plone.app.multilingual:default',
            'Products.ATContentTypes:default',
            'Products.PloneKeywordManager:default',
            'archetypes.multilingual:default',
            'plone.app.mosaic:default',
            'plone.app.drafts:default',
            'plone.app.blocks:default',
            'plone.app.openid:default'
            ]


FOOTER_HTML = """
<div class="row">
    <div class="col-sm-3">
        <h5>Connect with Us</h5>
        <ul class="footer-contact">
            <li><span class="icon icon-phone"></span><a href="tel:+17152526769">(715) 869-3440</a></li>
            <li><span class="icon icon-email"></span><a href="mailto:info@wildcardcorp.com">info@wildcardcorp.com</a></li>
            <li>
                <ul class="social-icons">
                    <li><a href="https://www.facebook.com/wildcardcorp"><span class="sr-only">Facebook</span><span class="icon icon-footer-fb"></span></a></li>
                    <li><a href="https://twitter.com/WildcardCorp"><span class="sr-only">Twitter</span><span class="icon icon-footer-twitter"></span></a></li>
                    <li><a href="https://www.linkedin.com/company/wildcard-corp-?trk=company_logo"><span class="sr-only">Linkedin</span><span class="icon icon-footer-linkedin"></span></a></li>
                </ul>
            </li>
        </ul>
    </div>
    <div class="col-sm-7 col-sm-offset-2">
        <h5>Get News & Updates</h5>
        <p>Sign up for product updates and the latest goings-ons from Wildcard Corp.</p>
        <form class="form-inline">
            <div class="form-group">
                <label class="sr-only" for="newsletter-email">Email Address</label>
                <div class="input-group">
                    <input type="email" class="form-control" id="newsletter-email" placeholder="Email Address">
                    <span class="input-group-btn">
                        <a href="#" class="btn btn-primary">Sign Up</a>
                    </span>
                </div>
            </div>
        </form>
    </div>
    <div class="col-sm-12">
        <p class="copyright">
            Copyright <abbr title="Copyright symbol" i18n:name="copyright" i18n:attributes="title title_copyright;">&copy;</abbr> %s by Wildcard Corp.
        </p> 
    </div>
</div>""" % DateTime().year()  # noqa


_tiles_data = {
    'footer': [{
        'data': {'content': FOOTER_HTML},
        'meta': {'type': 'plone.app.standardtiles.rawhtml',
                 'id': 'footer-html'}
    }]
}


def tiles(site, req, tiles_data=_tiles_data):

    alsoProvides(req, ICastleLayer)

    # Sitewide slot tiles
    for meta_id, tiles in tiles_data.items():
        meta_tile = MetaTile(site, req)
        alsoProvides(meta_tile, IGlobalTile)
        meta_tile.id = 'meta-' + meta_id
        meta_tile.__name__ = 'castle.cms.meta'
        meta_data_manager = ITileDataManager(meta_tile)
        meta_data = meta_data_manager.get()
        meta_tiles = []

        for tile_data in tiles:
            meta_tiles.append(tile_data['meta'])
            tile = getMultiAdapter((site, req), name=tile_data['meta']['type'])
            alsoProvides(tile, IPersistentTile)
            tile.id = tile_data['meta']['id']
            tile.__name__ = tile_data['meta']['type']
            data_manager = ITileDataManager(tile)
            data_manager.set(tile_data['data'])

        meta_data['tiles'] = meta_tiles
        meta_data_manager.set(meta_data)

    frontpage = site['front-page']
    adapted = ILayoutAware(frontpage, None)
    if adapted:
        adapted.pageSiteLayout = 'frontpage.html'

    # Tiles only for the front-page
    frontpage_tiles = getTileData()

    for tile in frontpage_tiles:
        fp_tile = getMultiAdapter((frontpage, req), name=tile['meta']['type'])

        meta = tile['meta']
        fp_tile.id = meta['id']
        alsoProvides(fp_tile, IPersistentTile)
        data_manager = ITileDataManager(fp_tile)
        data_manager.set(tile['data'])

        if 'slot' in tile:
            meta_tile = MetaTile(frontpage, req)
            alsoProvides(meta_tile, IGlobalTile)
            meta_tile.id = 'meta-' + tile['slot']
            meta_tile.__name__ = 'castle.cms.meta'
            meta_data_manager = ITileDataManager(meta_tile)
            meta_data = meta_data_manager.get()

            existing_tiles = meta_data.get('tiles') or []
            new_tile_id = tile['meta']['id']

            if new_tile_id in [x['id'] for x in existing_tiles]:
                # check if the tile we're trying to install is already there.
                continue

            existing_tiles.append(meta)
            meta_data['tiles'] = existing_tiles
            meta_data['mode'] = 'show'

            meta_data_manager.set(meta_data)

    frontpageLayout = ILayoutAware(frontpage, None)
    if frontpageLayout:
        frontpageLayout.contentLayout = '/++contentlayout++castle/frontpage-layout.html'  # noqa
