from Acquisition import aq_inner
from castle.cms.lockout import LockoutManager
from plone import api
from Products.CMFPlone.controlpanel.browser import usergroups_usersoverview
from zExceptions import Forbidden

import time


class UsersOverviewControlPanel(usergroups_usersoverview.UsersOverviewControlPanel):
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

    def initialize_memberdata(self):
        portal_memberdata = api.portal.get_tool("portal_memberdata")
        if not portal_memberdata.hasProperty("reset_password_required"):
            portal_memberdata.manage_addProperty(
                id="reset_password_required", value=False, type="boolean")
            portal_memberdata.manage_addProperty(
                id="reset_password_time", value=time.time(), type="float")

    def set_password(self):
        self.initialize_memberdata()
        userid = self.request.form.get('userid')
        pw = self.request.form.get('password')

        mtool = api.portal.get_tool('portal_membership')

        # marker to tell us we need to force user to reset password later
        user = api.user.get(userid)
        user.setMemberProperties(mapping={
            'reset_password_required': True,
            'reset_password_time': time.time()
        })

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
