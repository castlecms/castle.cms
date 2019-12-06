from castle.cms.interfaces import ISecureLoginAllowedView
from castle.cms.interfaces import IAuthenticator
from Products.PasswordResetTool.PasswordResetTool import ExpiredRequestError
from Products.PasswordResetTool.PasswordResetTool import InvalidRequestError
from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five import BrowserView
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implements
from zope.i18n import translate
from plone import api

import json


class PasswordResetView(BrowserView):
    implements(ISecureLoginAllowedView)

    def __init__(self, context, request):
        super(PasswordResetView, self).__init__(context, request)
        self.auth = self.authenticator = getMultiAdapter(
            (context, request), IAuthenticator)

    def __call__(self):
        if self.request.REQUEST_METHOD == 'POST':
            self.request.response.setHeader('Content-type', 'application/json')
            return self.reset_password()
        else:
            return self.index()

    def reset_password(self):
        pw_tool = api.portal.get_tool('portal_password_reset')
        registration = api.portal.get_tool('portal_registration')
        userid = self.request.form.get('userid')
        randomstring = self.request.form.get('code')
        password = self.request.form.get('password')

        err_str = registration.testPasswordValidity(password)
        if err_str is not None:
            return json.dumps({
                'success': False,
                'message': translate(err_str)
            })

        alsoProvides(self.request, IDisableCSRFProtection)
        try:
            pw_tool.resetPassword(userid, randomstring, password)
        except ExpiredRequestError:
            return json.dumps({
                'success': False,
                'message': 'Password reset request has expired'
            })
        except (InvalidRequestError, RuntimeError):
            return json.dumps({
                'success': False,
                'message': 'Password reset request is invalid'
            })

        return json.dumps({
            'success': True,
            'message': 'Password reset successfully'
        })

    def get_data(self):
        data = {
            'code': self.request.form.get('code'),
            'userid': self.request.form.get('userid'),
            'apiEndpoint': self.context.absolute_url() + '/@@password-reset',
            'successUrl': api.portal.get().absolute_url() + '/@@secure-login'
        }
        return json.dumps(data)
