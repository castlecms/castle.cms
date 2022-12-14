from castle.cms.tiles.base import BaseTile
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary

import re


class FacebookPageTile(BaseTile):
    def render(self):
        content = self.data.get('href', '') or ''

        urlRegEx = r".*facebook\.com/([a-zA-Z0-9]+)/?"
        urlParser = re.compile(urlRegEx)
        matches = urlParser.match(content)

        if matches is None:
            return ''

        self.pageID = matches.group(1)

        self.parameters = {}
        validFields = IFacebookPageTileSchema._InterfaceClass__attrs.keys()

        # Prevent any additional values from being passed to FB
        for key in self.data.keys():
            if key in validFields:
                self.parameters[key] = self.data.get(key, '')

        return self.index()


class IFacebookPageTileSchema(model.Schema):
    href = schema.URI(
        title=u"URL",
        description=u"URL to the Facebook page to include in the tile."
    )

    hide_cover = schema.Bool(
        title=u"Hide cover photo",
        description=u"Don't include the page's cover photo in the tile."
    )

    show_facepile = schema.Bool(
        title=u"Show friend's faces",
        description=u"Show friends of the current user who liked the page."
    )

    small_header = schema.Bool(
        title=u"Use small header",
        description=u"Show a smaller, less detailed header."
    )

    timeline = schema.Choice(
        title=u"Show timeline",
        description=u"Show past posts by the Facebook page being embedded.",
        vocabulary=SimpleVocabulary.fromValues(['', 'timeline', 'events'])
    )
