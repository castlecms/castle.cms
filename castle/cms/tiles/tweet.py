from castle.cms.tiles.base import BaseTile
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary

import json
import re


class TweetTile(BaseTile):
    def render(self):
        content = self.data.get('url', '') or ''

        urlRegEx = ".*twitter\.com/.*/status/([0-9]+)"
        urlParser = re.compile(urlRegEx)
        matches = urlParser.match(content)

        if matches is None:
            return ''

        tweetID = matches.group(1)
        options = {'tweetID': tweetID}

        options['settings'] = {}

        cards = self.data.get('cards', '')
        options['settings']['cards'] = cards

        self.patternOptions = json.dumps(options)
        self.portalUrl = self.context.portal_url()

        return self.index()


class ITweetTileSchema(model.Schema):
    url = schema.URI(
        title=u"URL",
        description=u"URL to the tweet to include in the tile."
    )

    cards = schema.Choice(
        title=u"Hide tweet card",
        default='visible',
        description=u"Whether or not to include any associate pictures or videos.",
        vocabulary=SimpleVocabulary.fromValues(['visible','hidden'])
    )
