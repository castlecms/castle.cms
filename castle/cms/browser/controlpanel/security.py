from castle.cms.interfaces import ISecuritySchema
from castle.cms.widgets import SelectFieldWidget
from plone.app.registry.browser import controlpanel
from Products.CMFPlone.controlpanel.browser import security
from z3c.form.field import Fields
from zope.schema import Int
from plone import api


class SecurityControlPanelForm(security.SecurityControlPanelForm):
    schema = ISecuritySchema

    def updateFields(self):
        super(SecurityControlPanelForm, self).updateFields()
        self.fields['restrict_logins_to_countries'].widgetFactory = SelectFieldWidget
        timeout = api.portal.get().acl_users.session.timeout
        timeout_field = Int(__name__='session_timeout',
                            title=u'Session Timeout',
                            description=u'Duration of user session timeout '
                                        u'(seconds)',
                            required=False,
                            default=timeout)
        self.fields += Fields(timeout_field)

    def applyChanges(self, data):
        super(SecurityControlPanelForm, self).applyChanges(data)
        timeout = int(data['session_timeout'])
        self.context.acl_users.session.timeout = timeout


class SecurityControlPanel(controlpanel.ControlPanelFormWrapper):
    form = SecurityControlPanelForm
