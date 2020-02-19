from Products.Five import BrowserView
from lxml import etree
from urlparse import urlparse, parse_qs
from plone.app.uuid.utils import uuidToObject


class SlideshowView(BrowserView):

    def get_slides(self):
        slides = []
        root = etree.fromstring(self.context.content)
        tiles = root.findall('.//{http://www.w3.org/1999/xhtml}div[@data-tile]')
        for tile in tiles:
            tile_path = tile.get('data-tile')
            if 'castle.cms.slide/' in tile_path:
                parsed = urlparse(tile_path)
                data = parse_qs(parsed.query)
                slide = {}
                try:
                    slide['text'] = data['text:text'][0]
                except Exception:
                    slide['text'] = None
                try:
                    image = uuidToObject(data['image:list'][0])
                    slide['image'] = image.absolute_url()
                except Exception:
                    slide['image'] = None
                try:
                    video = uuidToObject(data['video:list'][0])
                    slide['video'] = video.absolute_url()
                except Exception:
                    slide['video'] = None
                try:
                    slide['displayType'] = data['display_type'][0]
                except Exception:
                    slide['displayType'] = 'background-image'
                try:
                    slide['title'] = data['title'][0]
                except Exception:
                    slide['title'] = None
                slide['vert'] = data['vert_text_position'][0]
                slide['hor'] = data['hor_text_position'][0]
                slides.append(slide)
        return slides

    def get_id(self):
        return self.context.custom_dom_id or None
