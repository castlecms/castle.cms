from castle.cms.tiles.base import BaseTile
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary

import re


class TweetTile(BaseTile):
    def render(self):
        content = self.data.get('url', '') or ''
        self.theme = self.data.get('theme', 'light')

        urlRegEx = r".*twitter\.com/.*/status/([0-9]+)"
        urlParser = re.compile(urlRegEx)
        matches = urlParser.match(content)

        if matches is None:
            return ''

        self.embed_url = '{content}?ref_src=twsrc%5Etfw'.format(content=content)

        self.portalUrl = self.context.portal_url()

        return self.index()


class ITweetTileSchema(model.Schema):
    url = schema.URI(
        title=u"URL",
        description=u"URL to the tweet to include in the tile."
    )

    theme = schema.Choice(
        title=u"Theme",
        description=u"Timeline color scheme.",
        vocabulary=SimpleVocabulary.fromValues(['light', 'dark']),
        default='light',
        required=False
    )
