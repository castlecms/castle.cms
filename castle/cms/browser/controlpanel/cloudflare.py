from castle.cms.caching.cloudflare import ICloudflareSettings
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class CloudflareControlPanelForm(RegistryEditForm):
    schema = ICloudflareSettings
    id = "CloudflareControlPanel"
    label = u'Cloudflare Settings'

    control_panel_view = '@@cloudflare-controlpanel'

class CloudflareControlPanel(ControlPanelFormWrapper):
    form = CloudflareControlPanelForm
    index = ViewPageTemplateFile('templates/cloudflare.pt')
