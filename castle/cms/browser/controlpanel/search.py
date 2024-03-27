from Products.Five import BrowserView
from plone import api

from castle.cms.interfaces import ISearchExclusionSettings
from castle.cms.widgets import SelectFieldWidget
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from z3c.form import form


class ExclusionPanelForm(RegistryEditForm):
    form.extends(RegistryEditForm)
    schema = ISearchExclusionSettings

    label = u'Search Exclusion Settings'

    control_panel_view = '@@search-exclusion-controlpanel'

    def updateFields(self):
        super(ExclusionPanelForm, self).updateFields()
        self.fields['items_to_exclude'].widgetFactory = SelectFieldWidget


class ExclusionPanelFormWrapper(ControlPanelFormWrapper):

    def __init__(self, *args, **kwargs):
        super(ExclusionPanelFormWrapper, self).__init__(*args, **kwargs)

    def get_excluded_content(self):
        catalog = api.portal.get_tool('portal_catalog')
        excluded_content = catalog(exclude_from_search=True)
        return excluded_content


ExclusionPanelView = layout.wrap_form(
    ExclusionPanelForm,
    ExclusionPanelFormWrapper)


class PublishedWithPrivateParents(BrowserView):
    def get_published_private_parent_content(self):
        catalog = api.portal.get_tool('portal_catalog')
        content = catalog(review_state='published', has_private_parents=True)
        return content
