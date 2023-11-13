from collective.documentviewer.browser.controlpanel import GlobalSettingsForm
from plone.app.z3cform.layout import wrap_form
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile


class CastleDocumentViewerSettingsForm(GlobalSettingsForm):
    template = ViewPageTemplateFile('templates/documentviewer.pt')
    label = None
    description=None


GlobalSettingsFormView = wrap_form(CastleDocumentViewerSettingsForm)
