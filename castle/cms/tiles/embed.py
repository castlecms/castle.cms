from castle.cms.tiles.base import BaseTile
from plone import api
from plone.registry.interfaces import IRegistry
from plone.tiles.interfaces import IPersistentTile
from zope import schema
from zope.component import getUtility
from zope.interface import implements
from zope.interface import Interface


class EmbedTile(BaseTile):
    implements(IPersistentTile)

    def render(self):
        content = self.data.get('code', '') or ''
        site_url = portal_url = api.portal.get_tool('portal_url')
        site_url = portal_url()
        registry = getUtility(IRegistry)
        public_url = registry.get('plone.public_url', None)
        if not public_url:
            public_url = site_url
            if not api.user.is_anonymous():
                site_url = public_url
        context_url = self.context.absolute_url()
        return content.replace(
            '{context-url}', context_url).replace(
            '{public-url}', public_url).replace(
            '{site-url}', site_url)


class IEmbedTileSchema(Interface):

    code = schema.Text(
        title=u"Code",
        description=u"Raw html code to include"
    )
