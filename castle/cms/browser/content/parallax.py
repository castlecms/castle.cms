from lxml import etree
from plone.app.uuid.utils import uuidToObject
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

                # Parallax tile properties
                try:
                    image = uuidToObject(data['image:list'][0])
                    parallax_tile['image'] = image.absolute_url()
                except Exception:
                    parallax_tile['image'] = None

                parallax_tile['bg_color'] = data.get('bg_color', ['white'])[0]
                parallax_tile['title'] = data.get('title', [None])[0]
                parallax_tile['title_size'] = data.get('title_size', ['36px'])[0]
                parallax_tile['text'] = data.get('text:text', [None])[0]
                parallax_tile['text_size'] = data.get('text_size', ['12px'])[0]
                hor_position = data.get('hor_text_position', ['center'])[0]
                if hor_position == 'start':
                    parallax_tile['hor_left'] = '5%'
                    parallax_tile['hor_right'] = '45%'
                elif hor_position == 'end':
                    parallax_tile['hor_left'] = '45%'
                    parallax_tile['hor_right'] = '5%'
                else:
                    parallax_tile['hor_left'] = '10%'
                    parallax_tile['hor_right'] = '10%'
                    parallax_tile['justify_center'] = True
                parallax_tile['text_color'] = data.get('text_color', ['black'])[0]
                parallax_tile['text_shadow'] = data.get('text_shadow', [None])[0]

                # Static tile properties
                try:
                    image = uuidToObject(data['static_image:list'][0])
                    parallax_tile['static_image'] = image.absolute_url()
                except Exception:
                    parallax_tile['static_image'] = None

                parallax_tile['static_bg_color'] = data.get('static_bg_color', ['white'])[0]
                parallax_tile['static_title'] = data.get('static_title', [None])[0]
                parallax_tile['static_title_size'] = data.get('static_title_size', ['36px'])[0]
                parallax_tile['static_text'] = data.get('static_text:text', [None])[0]
                parallax_tile['static_text_size'] = data.get('static_text_size', ['12px'])[0]
                hor_position = data.get('static_hor_text_position', ['center'])[0]
                if hor_position == 'start':
                    parallax_tile['static_hor_left'] = '5%'
                    parallax_tile['static_hor_right'] = '45%'
                elif hor_position == 'end':
                    parallax_tile['static_hor_left'] = '45%'
                    parallax_tile['static_hor_right'] = '5%'
                else:
                    parallax_tile['static_hor_left'] = '10%'
                    parallax_tile['static_hor_right'] = '10%'
                    parallax_tile['static_justify_center'] = True
                parallax_tile['static_text_color'] = data.get('static_text_color', ['black'])[0]
                parallax_tile['static_text_shadow'] = data.get('static_text_shadow', [None])[0]

                parallax_tiles.append(parallax_tile)

        return parallax_tiles
