from castle.cms.interfaces import ISecuritySchema
from castle.cms.widgets import SelectFieldWidget
from plone.app.registry.browser import controlpanel
from Products.CMFPlone.controlpanel.browser import security


class SecurityControlPanelForm(security.SecurityControlPanelForm):
    schema = ISecuritySchema

    def updateFields(self):
        super(SecurityControlPanelForm, self).updateFields()
        self.fields['restrict_logins_to_countries'].widgetFactory = SelectFieldWidget


class SecurityControlPanel(controlpanel.ControlPanelFormWrapper):
    form = SecurityControlPanelForm
