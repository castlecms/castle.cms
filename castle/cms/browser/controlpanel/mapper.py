from plone.resource.manifest import MANIFEST_FILENAME
from plone.resource.manifest import getManifest
from plone.subrequest import subrequest
from plone.app.theming.browser.mapper import ThemeMapper as BaseThemeMapper
from castle.cms import theming
from plone import api
from plone.app.theming.utils import getTheme
from plone.app.theming.interfaces import MANIFEST_FORMAT


class ThemeMapper(BaseThemeMapper):

    def getFrame(self):
        theme_name = self.context.__name__
        theme = None
        if self.context.isFile(MANIFEST_FILENAME):
            manifest = self.context.openFile(MANIFEST_FILENAME)
            theme = getManifest(manifest, MANIFEST_FORMAT, None)
            theme['name'] = theme_name
            manifest.close()
        theme = getTheme(theme_name, theme)
        if theme.rules and theme.rules.endswith('.xml'):
            return super(ThemeMapper, self).getFrame()

        # we're assuming it is a castle type theme
        self.request.environ[theming.OVERRIDE_ENVIRON_KEY] = theme_name
        response = subrequest('/', root=api.portal.get())
        result = response.getBody()
        return result
