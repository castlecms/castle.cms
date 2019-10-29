from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from plone import api
from castle.cms.interfaces import IAuthenticator
from zope.i18n import translate
import json


class AccountUtilsView(BrowserView):
    def __init__(self, context, request):
        super(AccountUtilsView, self).__init__(context, request)
        self.auth = self.authenticator = getMultiAdapter(
            (context, request), IAuthenticator)

    def __call__(self):
        if api.user.is_anonymous():
            self.request.response.setStatus(403)
            return json.dumps({
                'reason': 'No account utils when signed out.'
            })
        # api_method = self.request.form.get('apiMethod')
        # change password will go here instead of secure login view
        # valid sesssion required to access this view

    def set_password(self):
        # 1. Authenticate user
        authorized, user = self.auth.authenticate(
            username=self.username,
            password=self.request.form.get('existing_password'),
            country=self.get_country_header(),
            login=False)

        if not user or not authorized:
            return json.dumps({
                'success': False,
                'message': 'Existing credentials did not match'
            })

        # 2. Set password
        newpw = self.request.form.get('new_password')

        registration = getToolByName(self.context, 'portal_registration')
        err_str = registration.testPasswordValidity(newpw)

        if err_str is not None:
            return json.dumps({
                'success': False,
                'message': translate(err_str)
            })

        mtool = api.portal.get_tool('portal_membership')
        member = mtool.getMemberById(user.getId())

        self.auth.change_password(member, newpw)

        self.auth.authenticate(
            username=self.username,
            password=newpw,
            country=self.get_country_header(),
            login=True)

        return json.dumps({
            'success': True
        })
