from zope import schema
from castle.cms.tiles.base import BaseTile
from castle.cms.browser.subscribe import SubscribeForm
from plone.supermodel import model
from plone import api
import requests, re, json

class SubscriptionTile(BaseTile, SubscribeForm):

    def initialize(self):
        portal = api.portal.get()
        self.request.URL = portal.absolute_url() + '/@@subscribe'
        self.label = self.data.get('title', '')

        self.update()

    def __init__(self, context, request):
        super(SubscriptionTile, self).__init__(context, request)
        self.initialize()

class ISubscriptionTileSchema(model.Schema):
    title = schema.TextLine(
        title=u"Title",
        default=u"Subscribe to email updates"
    )
