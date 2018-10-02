from castle.cms.browser.survey import ICastleSurvey
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class SurveyControlPanelForm(RegistryEditForm):
    schema = ICastleSurvey
    id = "SurveyControlPanel"
    label = u'GovSurvey.us Settings'
    description = "Engage your website vistors and request feedback and improvements or just ask some general questions! Signup with https://GovSurvey.us"  # noqa

    control_panel_view = '@@survey-controlpanel'


class SurveyControlPanel(ControlPanelFormWrapper):
    form = SurveyControlPanelForm
    index = ViewPageTemplateFile('templates/survey.pt')
