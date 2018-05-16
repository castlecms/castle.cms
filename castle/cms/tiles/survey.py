from castle.cms.tiles.base import BaseTile
from castle.cms.browser.survey import ICastleSurvey #CastleSurvey,
from zope import schema
from zope.interface import Interface
from plone import api
from plone.autoform.directives import widget
from z3c.form.browser.radio import RadioFieldWidget
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
import json

class SurveyTile(BaseTile):
    def initialize(self):
        portal = api.portal.get()
        self.request.URL = portal.absolute_url() + '/@@survey'
        self.label = self.data.get('title', '')
        survey_settings = getUtility(IRegistry).forInterface(ICastleSurvey, check=False)
        api_url = survey_settings.survey_api_url
        self.survey_url = self.data.get('survey', '') #"{}survey/{}".format(api_url, self.data.get('survey', ''))
        self.rule = self.data.get('rule', 'always')
        self.display = self.data.get('display', 'modal')
        self.duration = self.data.get('duration', 20)
        self.count = self.data.get('page_count', 5)
        self.tile_data = self.getData()

    def getData(self):
        import pdb; pdb.set_trace()
        survey_data = {
            'url': self.data.get('survey', ''),
            'rule': self.rule,
            'display': self.display,
            'duration': self.duration,
            'count': self.count
        }
        return json.dumps(survey_data)

    #def render(self):
    #    return self.index()

    def __init__(self, context, request):
        super(SurveyTile, self).__init__(context, request)
        self.initialize()

class ISurveyTileSchema(Interface):
    #Manually entering survey link and title needs to be an option as opped to just the list from API
    survey = schema.Choice(
       title=u'Surveys',
       description=u'Select the survey you\'d like to display.',
       required=True,
       vocabulary='castle.cms.vocabularies.Surveys'
    )

    rule = schema.Choice(
        title=u'Display Rules',
        description=u'When should the survey display?',
        required=True,
        vocabulary=SimpleVocabulary([
                        SimpleTerm(u'always', u'always', u'Always'),
                        SimpleTerm(u'timer', u'timer', u'Countdown/Timer: Visitor has been on this page for some time'),
                        SimpleTerm(u'count', u'count', u'Page Count: Visitor has gone to x number of pages'),
                        SimpleTerm(u'leave', u'leave', u'When Mouse Leaves top of page')
                    ]),
    )

    duration = schema.Int(
        title=u'Timer Duration',
        description=u'If Countdown/Timer rule selected, enter duration (seconds).',
        required=False
    )

    page_count = schema.Int(
        title=u'Page Count',
        description=u'If Page Count rule selected, enter number of pages',
        required=False
    )

    display = schema.Choice(
        title=u'Display Mode',
        description=u'Where should the survey display?',
        required=True,
        vocabulary=SimpleVocabulary([
                        SimpleTerm(u'modal',u'modal',u'As a Modal overlaying the page.'),
                        SimpleTerm(u'here',u'here',u'In the location this tile is placed.')
                    ])
    )
