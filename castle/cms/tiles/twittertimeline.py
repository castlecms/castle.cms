import json

from castle.cms.tiles.base import BaseTile
from plone.memoize.instance import memoize
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from zope import schema
from zope.component import getUtility
from zope.schema.vocabulary import SimpleVocabulary


class TwitterTimelineTile(BaseTile):
    def render(self):
        screenName = self.data.get('screenName', '')

        widgetID = self.get_widget_id()

        if widgetID is None or screenName is None:
            return ''

        parameters = {}
        validFields = ITwitterTimelineTileSchema._InterfaceClass__attrs.keys()

        # Prevent any additional values from being passed to Twitter
        for key in self.data.keys():
            if key in validFields:
                parameters[key] = self.data.get(key, '')

        if 'screenName' in parameters:
            if parameters['screenName'][0] == '@':
                parameters['screenName'] = parameters['screenName'][1:]

        options = {
            'widgetId': widgetID,
            'parameters': parameters
        }

        self.patternOptions = json.dumps(options)
        self.portalUrl = self.context.portal_url()

        return self.index()

    @memoize
    def get_widget_id(self):
        registry = getUtility(IRegistry)
        return registry.get('plone.twitter_timeline_widget')


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

    tweetLimit = schema.Int(
        title=u"Tweet limit",
        description=u"Maximum # of tweets to show (1-20)",
        min=1,
        default=10,
        max=20,
        required=False
    )

    theme = schema.Choice(
        title=u"Theme",
        description=u"Timeline color scheme.",
        vocabulary=SimpleVocabulary.fromValues(['light', 'dark']),
        default='light',
        required=False
    )
