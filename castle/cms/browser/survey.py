from zope.interface import Interface
from zope import schema
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import form


class ICastleSurvey(Interface):
    survey_api_url = schema.TextLine(
        title=u'GovSurvey API URL',
        description=u'GovSurvey.us API URL; https://govsurvey.us for more information.',
        required=False
    )

    survey_account_id = schema.TextLine(
        title=u'GovSurvey API Account ID',
        description=u'Account ID from your account on the GovSurvey system API',
        required=False
    )


class CastleSurvey(form.Form):
    label = u"Survey"
    description = u"A GovSurvey survey"
    formErrorsMessage = 'There were errors in a Castle Survey'
    ignoreContext = True
    schema = ICastleSurvey
    template = ViewPageTemplateFile("templates/survey.pt")
