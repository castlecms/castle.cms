from zope.interface import Interface
from zope import schema
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import form

class ICastleSurvey(Interface):
    survey_api_url = schema.TextLine(
        title=u'Survey API URL',
        description=u'API url for CastleCMS survey system',
        required=False
    )

    survey_account_id = schema.TextLine(
        title=u'Survey API Account ID',
        description=u'Account ID for survey system API',
        required=False
    )

class CastleSurvey(form.Form):
    label = u"Survey"
    description = u"A CastleCMS Survey"
    formErrorsMessage = 'There were errors in a Castle Survey'
    ignoreContext = True
    schema = ICastleSurvey
    template = ViewPageTemplateFile("templates/survey.pt")
