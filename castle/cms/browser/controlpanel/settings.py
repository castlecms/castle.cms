from castle.cms.interfaces import (
    IAdjustableFontSizeSettings,
    IAPISettings,
    IArchivalSettings,
    ICastleSettings,
    IContentSettings,
    ISiteConfiguration,
    ISearchSettings,
    IElasticSearchSettings,
    ISlideshowSettings,
)
from castle.cms.widgets import FileUploadFieldsFieldWidget, SelectFieldWidget
from plone.app.registry.browser import controlpanel
from plone.formwidget.namedfile.widget import NamedFileFieldWidget
from Products.CMFPlone import PloneMessageFactory as _
from z3c.form import field, group
from z3c.form.interfaces import HIDDEN_MODE


class APIForm(group.GroupForm):
    label = u"APIs"
    fields = field.Fields(IAPISettings)


class ArchivalForm(group.GroupForm):
    label = u"Archival"
    fields = field.Fields(IArchivalSettings)


class ContentForm(group.GroupForm):
    label = u"Content"
    fields = field.Fields(IContentSettings)


class ConfigurableTextForm(group.GroupForm):
    label = u"Configurable Text"
    fields = field.Fields(
        ISearchSettings,
        ISlideshowSettings,
        IAdjustableFontSizeSettings,
    )


class ElasticForm(group.GroupForm):
    label = u"Elastic Search"
    fields = field.Fields(IElasticSearchSettings)


class CastleSettingsControlPanelForm(controlpanel.RegistryEditForm):

    id = "CastleSettingsControlPanel"
    label = _(u"CastleCMS Settings")
    description = "Manage CastleCMS-specific settings"
    schema = ICastleSettings
    schema_prefix = "castle"
    fields = field.Fields(ISiteConfiguration)
    groups = (APIForm, ArchivalForm, ContentForm, ConfigurableTextForm, ElasticForm)

    def updateFields(self):
        super(CastleSettingsControlPanelForm, self).updateFields()
        self.groups[0].fields['google_api_service_key_file'].widgetFactory = NamedFileFieldWidget
        self.groups[1].fields['archival_types_to_archive'].widgetFactory = SelectFieldWidget
        self.groups[1].fields['archival_states_to_archive'].widgetFactory = SelectFieldWidget
        self.groups[2].fields['file_upload_fields'].widgetFactory = FileUploadFieldsFieldWidget

    def update(self):
        super(CastleSettingsControlPanelForm, self).update()
        self.groups[1].widgets["archival_replacements"].mode = HIDDEN_MODE


class CastleSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = CastleSettingsControlPanelForm
