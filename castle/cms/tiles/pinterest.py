from zope import schema
from castle.cms.tiles.base import BaseTile
from plone.supermodel import model


class PinTile(BaseTile):
    def render(self):
        if 'PIN_TILE' not in self.request.environ:
            self.renderJS = True
            self.request.environ['PIN_TILE'] = True
        else:
            self.renderJS = False

        return self.index()


class IPinTileSchema(model.Schema):

    url = schema.URI(
        title=u"URL of Pinterest Pin to embed.",
        required=True
    )
