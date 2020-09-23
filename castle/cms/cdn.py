from plone import api

class cdn(object):

    def __init__(self, hostname, port=80, path=''):
        self.hostname = api.portal.get_registry_record('castle.cdn_alternate_domain') or hostname
        self.port = api.portal.get_registry_record('castle.cdn_alternate_port') or port
        self.path = api.portal.get_registry_record('castle.cdn_alternate_path') or path
        self.js_allowed = api.portal.get_registry_record('castle.cdn_allow_js') or False
        self.css_allowed = api.portal.get_registry_record('castle.cdn_allow_css') or False
        self.images_allowed = api.portal.get_registry_record('castle.cdn_allow_images') or False

    def process_url(self, url, relative_path=''):

        # splits url parts
        protocol, path = url.split('://')
        path = path.split('/')
        hostname = self.hostname
        if self.port not in [80, ]:
            hostname = '%s:%s' % (hostname, self.port)

        path[0] = hostname
        # add path, if supplied
        if self.path:
            path.insert(1, self.path)

        # join everything
        path = '/'.join(path)
        url = '%s://%s' % (protocol, path)
        return url
