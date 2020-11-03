from plone import api


class CDN(object):

    def __init__(self, url_prefix):
        self.alternate_url = api.portal.get_registry_record('castle.cdn_alternate_url_prefix') or url_prefix
        self.modify_js_urls = api.portal.get_registry_record('castle.cdn_allow_js') or False
        self.modify_css_urls = api.portal.get_registry_record('castle.cdn_allow_css') or False
        self.modify_theming_urls = api.portal.get_registry_record('castle.cdn_allow_theming') or False
        self.modify_image_urls = api.portal.get_registry_record('castle.cdn_allow_images') or False

    def process_url(self, url):
        protocol, path = url.split('://')
        path = path.split('/')

        path[0] = self.alternate_url
        new_url = '/'.join(path)
        return new_url

    @property
    def configured_resources(self):
        return {'js': self.modify_js_urls, 'css': self.modify_css_urls,
                'image': self.modify_image_urls, 'theming': self.modify_theming_urls}
