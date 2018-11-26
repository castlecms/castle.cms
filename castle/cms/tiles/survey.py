from castle.cms.tiles.base import BaseTile
from castle.cms.browser.survey import ICastleSurvey
from zope import schema
from zope.interface import Interface
from Products.CMFPlone.utils import getSiteLogo
from plone.autoform.directives import widget
from z3c.form.browser.select import SelectWidget
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
import json
from base64 import b64encode


class SurveyTile(BaseTile):

    def getData(self):
        survey_settings = getUtility(IRegistry).forInterface(ICastleSurvey, check=False)
        survey_data = {
            'url': survey_settings.survey_api_url,
            'id': self.data.get('survey_id'),
            'custom_url': self.data.get('survey_url'),
            'rule': self.data.get('rule', 'always'),
            'cookie': self.data.get('use_cookie', 'show_once'),
            'display': self.data.get('display', 'here'),
            'duration': self.data.get('duration', 20),
            'count': self.data.get('page_count', 5),
            'logo': getSiteLogo()
        }
        return b64encode(json.dumps(survey_data))

    def render(self):
        if self.context.portal_membership.isAnonymousUser():
            return "<div class='pat-survey mosaic-survey-tile' data-pat-survey='{data}'/>".format(data=self.getData())  # noqa
        return "<div>Survey Tile: Some visitors will see an invitation.</div>"


class SurveyAPIWidget(SelectWidget):
    def render(self):
        for item in self.items:
            if item['value'] == 'no_api':
                return '<div class="survey-no-api">The CastleCMS Survey API is not configured properly.<br>Please enter a custom URL below, or finish configuring Survey in Site Settings.</div>'  # noqa
        return super(SurveyAPIWidget, self).render()


class ISurveyTileSchema(Interface):
    widget('survey_id', SurveyAPIWidget)
    survey_id = schema.Choice(
       title=u'Surveys',
       description=u'Select a survey from the API:',
       required=False,
       vocabulary='castle.cms.vocabularies.Surveys'
    )

    survey_url = schema.TextLine(
        title=u'Custom Survey URL',
        description=u'Or enter a survey URL manually:',
        required=False
    )

    rule = schema.Choice(
        title=u'Display Rules',
        description=u'When should the survey display?',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm(u'always', u'always', u'Immediately on each page effected by this tile'),
            SimpleTerm(u'timer', u'timer', u'Countdown/Timer: Visitor has been on this page for some time'),
            SimpleTerm(u'count', u'count', u'Page Count: Visitor has gone to x number of pages'),
            SimpleTerm(u'leave', u'leave', u'When Mouse Leaves top of page')
        ]),
    )

    use_cookie = schema.Choice(
        title=u'Cookies',
        description=u'How should cookies be used to prevent users from seeing the invite repeatedly?',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm(u'always', u'always', u'Always show the invite based on selected rules'),
            SimpleTerm(u'until_clicked', u'until_clicked', u'Show the invite only until the user clicks it'),
            SimpleTerm(u'show_once', u'show_once', u'Show the invite only once per session')
        ])
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
            SimpleTerm(u'modal', u'modal', u'As a Modal overlaying the page.'),
            SimpleTerm(u'here', u'here', u'In the location this tile is placed.')
        ])
    )
