import logging
from cStringIO import StringIO

from castle.cms.browser.files.files import NamedFileDownload
from castle.cms.interfaces import ISecureLoginAllowedView
from castle.cms.utils import site_has_icon
from PIL import Image
from plone import api
from plone.formwidget.namedfile.converter import b64decode_file
from plone.namedfile.file import NamedImage
from plone.registry.interfaces import IRegistry
from zExceptions import NotFound
from zope.component import getUtility
from zope.interface import implements


logger = logging.getLogger('castle.cms')


class IconView(NamedFileDownload):
    """
    a bit insane all the icon sizes we need but this is the world we live in...


<link rel="apple-touch-icon" sizes="180x180" href="/site-icon.png">
<link rel="icon" type="image/png" href="/site-icon.png?scale=32" sizes="32x32">
<link rel="icon" type="image/png" href="//site-icon.png?scale=16" sizes="16x16">
<link rel="manifest" href="/manifest.json">

<!-- can't do this one!!! no way to convert to svg -->
<link rel="mask-icon" href="/site-icon.svg" color="#5bbad5">

<meta name="theme-color" content="#ffffff">


from PIL import Image
filename = r'logo.png'
img = Image.open(filename)
icon_sizes = [(16,16), (32, 32), (48, 48), (64,64)]
img.save('logo.ico', sizes=icon_sizes)

    """
    implements(ISecureLoginAllowedView)

    filename = 'icon.png'

    allowed_sizes = (
        16,
        32,
        150,
        180,
        192,
        512
    )

    def get_data(self):
        registry = getUtility(IRegistry)
        try:
            data = registry['plone.site_icon']
        except Exception:
            data = None
        if data:
            filename, data = b64decode_file(data)
            return data

    def scale_data(self, data, scale):
        result = StringIO()
        image = Image.open(StringIO(data))
        image.thumbnail((scale, scale))
        image.save(result, "PNG")
        result.seek(0)
        return result.read()

    def _getFile(self):
        scale = None
        if 'scale' in self.request.form:
            try:
                scale = min(
                    abs(int(self.request.form['scale'])), 10000)
            except Exception:
                pass
        data = self.get_data()
        if data:
            if scale is not None:
                if scale in self.allowed_sizes:
                    data = self.scale_data(data, scale)
                else:
                    raise NotFound
            return NamedImage(data=data, filename=self.filename)


class FaviconView(IconView):
    filename = 'favicon.ico'

    def scale_data(self, data):
        result = StringIO()
        image = Image.open(StringIO(data))
        image.save(result, "ICO")
        result.seek(0)
        return result.read()

    def _getFile(self):
        data = self.get_data()
        if data:
            try:
                data = self.scale_data(data)
            except ValueError:
                logger.info('Error scaling favicon data', exc_info=True)
                raise NotFound
            return NamedImage(data=data, filename=self.filename)


class ManifestView(NamedFileDownload):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        title = api.portal.get_registry_record('plone.short_site_title')
        if not title:
            title = api.portal.get_registry_record('plone.site_title')
        if not site_has_icon():
            return '{"name": "%(site_title)s"}' % dict(site_title=title)

        return '''{
    "name": "%(site_title)s",
    "icons": [
        {
            "src": "%(url)s/site-icon.png?scale=192",
            "sizes": "192x192",
            "type": "image\/png"
        },
        {
            "src": "%(url)s/site-icon.png?scale=512",
            "sizes": "512x512",
            "type": "image\/png"
        }
    ],
    "theme_color": "#ffffff",
    "display": "standalone"
}''' % dict(url=self.context.absolute_url(),
            site_title=title)


class BrowserConfigView(NamedFileDownload):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'text/xml')
        if not site_has_icon():
            return '''<?xml version="1.0" encoding="utf-8"?>
    <browserconfig>
    </browserconfig>'''

        return '''<?xml version="1.0" encoding="utf-8"?>
<browserconfig>
  <msapplication>
    <tile>
      <square150x150logo src="{url}/site-icon.png?scale=150"/>
      <TileColor>#da532c</TileColor>
    </tile>
  </msapplication>
</browserconfig>
'''.format(url=self.context.absolute_url())
