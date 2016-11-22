from castle.cms.interfaces import IBusinessData
from castle.cms.widgets import MapPointFieldWidget
from plone.app.registry.browser import controlpanel
from z3c.form.browser.checkbox import CheckBoxFieldWidget


class BusinessControlPanelForm(controlpanel.RegistryEditForm):
    schema = IBusinessData
    schema_prefix = 'castle'
    id = "BusinessControlPanel"
    label = u"Business Settings"
    description = ""

    def updateFields(self):
        super(BusinessControlPanelForm, self).updateFields()
        self.fields['business_coordinates'].widgetFactory = MapPointFieldWidget
        self.fields['business_days_of_week'].widgetFactory = CheckBoxFieldWidget


class BusinessControlPanel(controlpanel.ControlPanelFormWrapper):
    form = BusinessControlPanelForm
