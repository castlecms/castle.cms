from zope.interface import Interface
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import form
from z3c.form import button


class ICastleSurvey(Interface):
    pass

class CastleSurvey(form.Form):
    label = u"Survey"
    description = u"A CastleCMS Survey"
    formErrorsMessage = 'There were errors in a Castle Survey'
    ignoreContext = True
    schema = ICastleSurvey
    template = ViewPageTemplateFile("templates/survey.pt")
