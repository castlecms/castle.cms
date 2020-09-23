from plone.registry.interfaces import IRegistry
from zope.component import getUtility

class cdn(object):

    def __init__(self, hostname=[], port=80, path=''):
        registry = getUtility(IRegistry)

        self.hostname = registry.get('castle.cdn_alternate_domain', None) or hostname
        self.port = registry.get('castle.cdn_alternate_port', None) or port
        self.path = registry.get('castle.cdn_alternate_path', None) or  path
        self.js_allowed = registry.get('castle.cdn_allow_js', None) or False
        self.css_allowed = registry.get('castle.cdn_allow_css', None) or False
        self.images_allowed = registry.get('castle.cdn_allow_images', None) or False

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
