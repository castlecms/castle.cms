from zope.interface import Interface
from zope import schema
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import form
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from plone.protect.interfaces import IDisableCSRFProtection
from zope.interface import alsoProvides
import requests

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

    #def __init__(self, context, request):
    #    super(CastleSurvey, self).__init__(context, request)
    #    alsoProvides(request, IDisableCSRFProtection)
    #    registry = getUtility(IRegistry)
    #    survey_settings = registry.forInterface(ICastleSurvey, check=False)
        #api_url = survey_settings.survey_api_url
        #api_key = survey_settings.survey_api_key
        #data = '''{
        #}'''
        #surveys = requests.post(api_url,data=data)
        #surveys = [u'newurl|New', u'newurl2|Test', u'newurl3|Stuff']
        #registry['castle.survey_list'] = surveys
