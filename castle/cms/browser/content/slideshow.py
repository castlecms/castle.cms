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
                if slide['displayType'] == 'resource-slide':
                    try:
                        related_uuids = data['related_items:list']
                        slide['related_resources'] = [uuidToObject(uuid) for uuid in related_uuids]
                    except Exception:
                        pass
                slide['vert'] = data['vert_text_position'][0]
                slide['hor'] = data['hor_text_position'][0]
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
