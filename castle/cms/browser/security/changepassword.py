from Products.CMFCore.utils import getToolByName
from plone import api
from Products.CMFPlone import PloneMessageFactory as _
from plone.app.users.browser.passwordpanel import PasswordPanel
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
import six
from DateTime import DateTime


class ChangePassword(PasswordPanel):

    @button.buttonAndHandler(
        _(u'label_change_password', default=u'Change Password'),
        name='reset_passwd'
    )
    def action_reset_passwd(self, action):
        data, errors = self.extractData()

        # extra password validation
        self.validate_password(action, data)

        if action.form.widgets.errors:
            self.status = self.formErrorsMessage
            return

        membertool = getToolByName(self.context, 'portal_membership')

        password = data['new_password']
        if six.PY2 and isinstance(password, six.text_type):
            password = password.encode('utf8')

        try:
            membertool.setPassword(password, None, REQUEST=self.request)
        except AttributeError:
            failMessage = _(u'While changing your password an AttributeError '
                            u'occurred. This is usually caused by your user '
                            u'being defined outside the portal.')

            IStatusMessage(self.request).addStatusMessage(
                _(failMessage), type="error"
            )
            return

        # handle PW expiry in Plone's change-password form
        user = api.user.get_current()
        user.setMemberProperties(mapping={
            'reset_password_required': False,
            'password_date': DateTime()
        })

        IStatusMessage(self.request).addStatusMessage(
            _("Password changed"), type="info"
        )
