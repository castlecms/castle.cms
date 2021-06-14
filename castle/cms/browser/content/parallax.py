from lxml import etree
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.browser import edit
from Products.CMFPlone.resources import add_resource_on_request
from Products.Five import BrowserView
from urlparse import urlparse, parse_qs


class ParallaxView(BrowserView):

    def get_tiles(self):
        parallax_tiles = []
        root = etree.fromstring(self.context.content)
        tiles = root.findall('.//{http://www.w3.org/1999/xhtml}div[@data-tile]')
        for tile in tiles:
            tile_path = tile.get('data-tile')
            if 'castle.cms.parallaxtile/' in tile_path:
                parsed = urlparse(tile_path)
                data = parse_qs(parsed.query)
                parallax_tile = {}
                try:
                    image = uuidToObject(data['image:list'][0])
                    parallax_tile['image'] = image.absolute_url()
                except Exception:
                    parallax_tile['image'] = None

                parallax_tiles.append(parallax_tile)

        return parallax_tiles
