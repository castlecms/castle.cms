from castle.cms.tiles.base import BaseTile
from castle.cms.browser.survey import ICastleSurvey
from zope import schema
from zope.interface import Interface
from plone import api
from plone.autoform.directives import widget
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
import json

class SurveyTile(BaseTile):

    def getData(self):
        portal = api.portal.get()
        survey_settings = getUtility(IRegistry).forInterface(ICastleSurvey, check=False)
        survey_data = {
            'url': survey_settings.survey_api_url,
            'id': self.data.get('survey_id'),
            'rule': self.data.get('rule', 'always'),
            'display': self.data.get('display','here'),
            'duration': self.data.get('duration', 20),
            'count': self.data.get('page_count', 5)
        }
        return json.dumps(survey_data)

    def render(self):
        if self.context.portal_membership.isAnonymousUser():
            return "<div class='pat-survey mosaic-survey-tile' data-pat-survey='{data}'/>".format(data=self.getData())
        return "<div>Survey Tile: Some visitors will see an invitation.</div>"


class ISurveyTileSchema(Interface):
    #Manually entering survey link and title needs to be an option as opposed to just the list from API
    survey_id = schema.Choice(
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
