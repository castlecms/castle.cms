from castle.cms.tiles.base import BaseTile
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary


class TwitterTimelineTile(BaseTile):
    def render(self):
        self.screenName = self.data.get('screenName', '')

        if self.screenName is None:
            return

        if self.screenName[0] == '@':
            self.sreenName = self.screenName[1:]

        self.height = self.data.get('height', '400')
        self.theme = self.data.get('theme', 'light')
        self.embed_url = 'https://twitter.com/{screenname}?ref_src=twsrc%5Etfw'.format(
            screenname=self.screenName)
        self.portalUrl = self.context.portal_url()

        return self.index()


class ITwitterTimelineTileSchema(model.Schema):
    screenName = schema.TextLine(
        title=u"Screen Name",
        description=u"Screen name of the user whose timeline you want to embed."
    )

    height = schema.Int(
        title=u"Height",
        description=u"Height of the rendered timeline, in pixels.",
        default=400,
        min=200,
        required=False
    )

    theme = schema.Choice(
        title=u"Theme",
        description=u"Timeline color scheme.",
        vocabulary=SimpleVocabulary.fromValues(['light', 'dark']),
        default='light',
        required=False
    )
