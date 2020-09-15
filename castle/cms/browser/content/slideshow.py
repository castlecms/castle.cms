from plone.dexterity.browser import edit
from Products.Five import BrowserView
from lxml import etree
from urlparse import urlparse, parse_qs
from plone.app.uuid.utils import uuidToObject
from plone.api.portal import get as get_portal
from plone.api.portal import get_registry_record
from plone.api.portal import set_registry_record
from Products.CMFPlone.resources import add_resource_on_request


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
                    image = uuidToObject(data['image:list'][0])
                    slide['image'] = image.absolute_url()
                except Exception:
                    slide['image'] = None
                try:
                    video = uuidToObject(data['video:list'][0])
                    slide['video'] = video.absolute_url()
                except Exception:
                    slide['video'] = None
                slide['displayType'] = data.get('display_type', ['background-image'])[0]
                if slide['displayType'] == 'resource-slide':
                    try:
                        related_uuids = data['related_items:list']
                        slide['related_resources'] = [uuidToObject(uuid) for uuid in related_uuids]
                    except Exception:
                        pass
                slide['title'] = data.get('title', [None])[0]
                slide['text'] = data.get('text:text', [None])[0]
                slide['vert'] = data.get('vert_text_position', ['middle'])[0]
                hor_text_position = data.get('hor_text_position', ['center'])[0]
                slide['hor'] = hor_text_position
                slide['width_class'] = 'full-width' if hor_text_position == 'center' else 'half-width'
                justify_wrapped_text = data.get('justify_wrapped_text:boolean', [0])[0] == '1'
                slide['justify_wrapped_text'] = justify_wrapped_text
                slide['justify_wrap_class'] = 'justify-wrap' if justify_wrapped_text else ''
                slide['text_alignment'] = data.get('text_alignment', ['center'])[0]
                slide['customize_left_slide_mobile'] = \
                    data.get('customize_left_slide_mobile:boolean', [0])[0] == '1'
                if slide['customize_left_slide_mobile']:
                    slide['left_mobile_hor'] = \
                        data.get('left_slide_mobile_hor_text_position', ['default'])[0]
                    slide['left_mobile_vert'] = \
                        data.get('left_slide_mobile_vert_text_position', ['default'])[0]
                    slide['left_mobile_alignment'] = \
                        data.get('left_slide_mobile_text_alignment', ['default'])[0]
                slides.append(slide)
        return slides

    def get_id(self):
        return self.context.custom_dom_id or None

    def get_view_more_link_text(self):
        try:
            return self.context.view_more_link_text
        except Exception:
            return None

    def get_view_more_link_url(self):
        try:
            return self.context.view_more_link_url
        except Exception:
            return None

    def display_view_more_link(self):
        try:
            show_view_more = self.context.show_view_more_link
        except Exception:
            show_view_more = True
        return (show_view_more and
                self.get_view_more_link_text() and
                self.get_view_more_link_url())

    def get_textlines(self, slide):
        slide_text = slide.get('text', '')
        if slide_text:
            return slide_text.split('\n')
        else:
            return None

    def get_resource_view_url(self, resource):
        view_types = get_registry_record('plone.types_use_view_action_in_listings') or []
        url = resource.absolute_url()
        if resource.portal_type in view_types:
            url += '/view'
        return url

    def get_domain(self):
        full_url = get_portal().absolute_url()
        domain = full_url.replace('https://', '').replace('http://', '')
        return domain

    def get_left_slide_mobile_options(self, slide):
        if slide.get('customize_left_slide_mobile', False):
            hor = slide.get('left_mobile_hor', 'default')
            vert = slide.get('left_mobile_vert', 'default')
            align = slide.get('left_mobile_alignment', 'default')
        else:
            hor = 'default'
            vert = 'default'
            align = 'default'
        return{
            'mobile_hor': slide.get('hor', 'center') if hor == 'default' else hor,
            'mobile_vert': slide.get('vert', 'middle') if vert == 'default' else vert,
            'mobile_alignment': slide.get('text_alignment', 'center') if align == 'default' else align,
        }


class SlideshowEditForm(edit.DefaultEditForm):
    def __call__(self, *args, **kw):
        add_resource_on_request(self.request, 'castle-components-slide')
        return super(SlideshowEditForm, self).__call__(*args, **kw)

    def update(self):
        super(SlideshowEditForm, self).update()

    def applyChanges(self, data):
        self.handle_update_default(data, 'link_text')
        self.handle_update_default(data, 'link_url')
        super(SlideshowEditForm, self).applyChanges(data)

    def handle_update_default(self, data, type):
        should_update_registy = data.get('update_default_{}'.format(type), False)
        form_value = data.get('view_more_{}'.format(type), None)
        if should_update_registy and form_value:
            record_name = 'castle.resource_slide_view_more_{}'.format(type)
            try:
                default_value = get_registry_record(record_name)
            except Exception:
                return
            if form_value != default_value:
                set_registry_record(record_name, form_value)
        data['update_default_{}'.format(type)] = False


SlideshowEditView = SlideshowEditForm
