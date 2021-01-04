from Acquisition import aq_inner
from castle.cms.lockout import LockoutManager
from castle.cms.passwordvalidation.nist import NISTPasswordValidator
from plone import api
from Products.CMFPlone.controlpanel.browser import usergroups_usersoverview
from Products.CMFPlone.resources import add_resource_on_request
from zExceptions import Forbidden

import time


class UsersOverviewControlPanel(usergroups_usersoverview.UsersOverviewControlPanel):
    def __call__(self):
        # utility function to add resource to rendered page
        add_resource_on_request(self.request, 'castle-components-usersgroups')

        # Sets properties for nist password validation if it is enabled
        nist_enabled = api.portal.get_registry_record('plone.nist_password_mode', default=False)
        if nist_enabled:
            self.nistEnabled = True
            self.get_nist_config()

        return super(UsersOverviewControlPanel, self).__call__()

    def manageUser(self, users=[], resetpassword=[], delete=[]):
        super(UsersOverviewControlPanel, self).manageUser(
            users=users, resetpassword=resetpassword, delete=delete)
        # custom actions here...
        action = self.request.form.get('action')
        if action == 'disable':
            self.disable_user()
        if action == 'enable':
            self.enable_user()
        elif action == 'delete':
            self.delete_user()
        elif action == 'setpassword':
            self.set_password()
        elif action == 'sendpwreset':
            self.send_pwreset()
        elif action == 'resetattempts':
            self.clear_login_attempts()
        elif action == 'togglewhitelist':
            self.toggle_whitelist()

    def disable_user(self):
        # disabling user is just unassigning all roles...
        userid = self.request.form.get('userid')

        mtool = api.portal.get_tool('portal_membership')
        acl_users = api.portal.get_tool('acl_users')

        member = mtool.getMemberById(userid)
        acl_users.userFolderEditUser(
            userid, None, [], member.getDomains(), REQUEST=self.context.REQUEST)

    def enable_user(self):
        # disabling user is just unassigning all roles...
        userid = self.request.form.get('userid')

        mtool = api.portal.get_tool('portal_membership')
        acl_users = api.portal.get_tool('acl_users')

        member = mtool.getMemberById(userid)
        acl_users.userFolderEditUser(
            userid, None, ['Member'], member.getDomains(), REQUEST=self.context.REQUEST)

    def clear_login_attempts(self):
        userid = self.request.form.get('userid')
        user = api.user.get(userid)
        lockout = LockoutManager(self.context, userid)
        lockout.clear()
        lockout = LockoutManager(self.context, user.getUserName())
        lockout.clear()

    def toggle_whitelist(self):
        userid = self.request.form.get('userid')
        user = api.user.get(userid)
        whitelist = api.portal.get_registry_record(
            'plone.pwexpiry_whitelisted_users'
        )
        if not whitelist:
            whitelist = []
        if whitelist and user.getId() in whitelist:
            whitelist.remove(user.getId())
        else:
            whitelist.append(user.getId().decode('utf-8'))
        api.portal.set_registry_record(
            'plone.pwexpiry_whitelisted_users',
            whitelist
        )

    def delete_user(self):
        """
        a modified version that does not go through all content
        and reindex
        """

        userid = self.request.form.get('userid')
        # this method exists to bypass the 'Manage Users' permission check
        # in the CMF member tool's version
        context = aq_inner(self.context)

        mtool = api.portal.get_tool('portal_membership')
        acl_users = api.portal.get_tool('acl_users')

        # Delete members in acl_users.
        acl_users = context.acl_users
        member = mtool.getMemberById(userid)
        if not member.canDelete():
            raise Forbidden
        if 'Manager' in member.getRoles() and not self.is_zope_manager:
            raise Forbidden
        try:
            acl_users.userFolderDelUsers([userid])
        except (AttributeError, NotImplementedError):
            raise NotImplementedError('The underlying User Folder '
                                      'doesn\'t support deleting members.')

        # Delete member data in portal_memberdata.
        mdtool = api.portal.get_tool('portal_memberdata')
        if mdtool is not None:
            mdtool.deleteMemberData(userid)

    def set_password(self):
        userid = self.request.form.get('userid')
        pw = self.request.form.get('password')
        user = api.user.get(userid)
        nist_enabled = api.portal.get_registry_record('plone.nist_password_mode', default=False)

        if nist_enabled:
            nist = NISTPasswordValidator(None)
            failed_validation = nist.validate(pw, check_history=True, user=user)
            if failed_validation:
                #! if the history validation fails, the password will not be changed,
                #! but it acts as if password change was successful.
                #TODO: Need to prevent form submission and indicate it to user.
                import pdb; pdb.set_trace()
                return failed_validation

        # marker to tell us we need to force user to reset password later
        user.setMemberProperties(mapping={
            'reset_password_required': True,
            'reset_password_time': time.time()
        })

        mtool = api.portal.get_tool('portal_membership')
        member = mtool.getMemberById(userid)
        member.setSecurityProfile(password=pw)

    def send_pwreset(self):
        userid = self.request.form.get('userid')

        mtool = api.portal.get_tool('portal_membership')
        regtool = api.portal.get_tool('portal_registration')
        acl_users = api.portal.get_tool('acl_users')

        member = mtool.getMemberById(userid)
        current_roles = member.getRoles()

        if 'Manager' in current_roles and not self.is_zope_manager:
            raise Forbidden

        pw = regtool.generatePassword()
        acl_users.userFolderEditUser(
            userid, pw, current_roles, member.getDomains(), REQUEST=self.context.REQUEST)

        self.context.REQUEST.form['new_password'] = pw
        regtool.mailPassword(userid, self.context.REQUEST)

    def get_nist_config(self):
        nist = NISTPasswordValidator(None)
        self.nistLength = nist.props['length']
        self.nistUpper = nist.props['uppercase']
        self.nistLower = nist.props['lowercase']
        self.nistSpecial = nist.props['special']
