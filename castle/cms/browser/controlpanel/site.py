from castle.cms.interfaces import ISiteSchema
from plone.app.registry.browser import controlpanel
from plone.formwidget.namedfile.widget import NamedFileFieldWidget
from Products.CMFPlone.controlpanel.browser import site
from z3c.form.browser.checkbox import CheckBoxFieldWidget


class SiteControlPanelForm(site.SiteControlPanelForm):
    schema = ISiteSchema

    def updateFields(self):
        super(SiteControlPanelForm, self).updateFields()
        self.fields['roles_allowed_to_add_keywords'].widgetFactory = CheckBoxFieldWidget
        self.fields['site_icon'].widgetFactory = NamedFileFieldWidget


class SiteControlPanel(controlpanel.ControlPanelFormWrapper):
    form = SiteControlPanelForm
