from castle.cms.tiles.base import BaseTile
from castle.cms.browser.survey import CastleSurvey
from zope import schema
from zope.interface import Interface
from plone import api
from plone.autoform.directives import widget
from z3c.form.browser.radio import RadioFieldWidget

class SurveyTile(BaseTile, CastleSurvey):
    def initialize(self):
        portal = api.portal.get()
        self.request.URL = portal.absolute_url() + '/@@survey'
        self.label = self.data.get('title', '')

        self.update()

    def __init__(self, context, request):
        super(SurveyTile, self).__init__(context, request)
        self.initialize()

class ISurveyTileSchema(Interface):
    widget('survey', RadioFieldWidget)
    survey = schema.List(
        title=u'Surveys',
        description=u'Select the survey you\'d like to display.',
        required=True,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.Surveys'
        )
    )
