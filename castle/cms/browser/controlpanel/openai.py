from plone.app.registry.browser.controlpanel import (
    RegistryEditForm,
    ControlPanelFormWrapper,
)
from plone.supermodel import model

import zope.schema as schema

class IOpenAISettings(model.Schema):
    openai_api_key = schema.TextLine(
        title=u'OpenAI API Key',
        default=None,
        required=False,
    )

class OpenAISettingsControlPanelForm(RegistryEditForm):
    schema_prefix = 'fbigov.theme'
    schema = IOpenAISettings
    id = 'OpenAISettingsControlPanel'
    label = u'OpenAI Settings'
    description = 'Settings to communicate with OpenAI API'


class OpenAISettingsControlPanel(ControlPanelFormWrapper):
    form = OpenAISettingsControlPanelForm
