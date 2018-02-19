from castle.cms.caching.cloudflare import ICloudflareSettings
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
#from z3c.form import form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
#from plone.z3cform import layout

class CloudflareControlPanelForm(RegistryEditForm):
    #form.extends(RegistryEditForm)
    schema = ICloudflareSettings
    id = "CloudflareControlPanel"
    label = u'Cloudflare Settings'

    control_panel_view = '@@cloudflare-controlpanel'

class CloudflareControlPanel(ControlPanelFormWrapper):
    form = CloudflareControlPanelForm
    index = ViewPageTemplateFile('templates/cloudflare.pt')

    # def __init__(self, *args, **kwargs):
    #     super(CloudflareControlPanelFormWrapper, self).__init__(*args, **kwargs)

# CloudflareControlPanelView = layout.wrap_form(
#     CloudflareControlPanelForm,
#     CloudflareControlPanelFormWrapper)
