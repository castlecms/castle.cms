from castle.cms.interfaces import IBusinessData
from castle.cms.widgets import MapPointFieldWidget
from plone.app.registry.browser import controlpanel
from z3c.form.browser.checkbox import CheckBoxFieldWidget


class BusinessControlPanelForm(controlpanel.RegistryEditForm):
    schema = IBusinessData
    schema_prefix = 'castle'
    id = "BusinessControlPanel"
    label = u"Google Business Settings"
    description = "Show you're open for business. This information will appear in Google Search and Maps. See https://www.google.com/business for details."  # noqa

    def updateFields(self):
        super(BusinessControlPanelForm, self).updateFields()
        self.fields['business_coordinates'].widgetFactory = MapPointFieldWidget
        self.fields['business_days_of_week'].widgetFactory = CheckBoxFieldWidget


class BusinessControlPanel(controlpanel.ControlPanelFormWrapper):
    form = BusinessControlPanelForm
