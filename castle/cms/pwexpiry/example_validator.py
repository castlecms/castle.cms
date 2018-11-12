from .config import _
from AccessControl import AuthEncoding
from castle.cms.pwexpiry.interfaces import ICustomPasswordValidator
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope.interface import implementer

import re


@implementer(ICustomPasswordValidator)
class ADPasswordValidator(object):
    """
    Validator for user's passwords fitting default MS Active Directory
    password policy.
    """

    def __init__(self, context):
        self.context = context

    def validate(self, password, data):
        """
        Password validation method
        """

        # Permit empty passwords here to allow registration links.
        # Plone will force the user to set one.
        if password is None:
            return None

        # Checking if minimal length of the entered password
        # is greater than 8 chars
        if len(password) < 8:
            return _(u'Passwords must be at least 8 characters in length.')

        # password is compared to unicode values
        password = safe_unicode(password)

        if not data:
            # setting password not from the registration form
            # we can obtain the existing user's properties instead of
            # collecting them from the submitted form
            data = {}
            pm = getToolByName(self.context, 'portal_membership')
            acl = getToolByName(self.context, 'acl_users')
            if pm.isAnonymousUser():
                userid = self.context.REQUEST.form.get('userid')
            else:
                userid = pm.getAuthenticatedMember().getProperty('id')
            member = pm.getMemberById(userid)
            if member:
                data['fullname'] = member.getProperty('fullname')
                data['username'] = userid
                data['prevhash'] = acl.source_users._user_passwords.get(userid)

        # Checking if the entered password doesn't contain
        # the user's username or any parts of his fullname
        for name in data.get('fullname', u'').split(' ') + \
                [data.get('username', ''), ]:
            if name:
                if not isinstance(name, unicode):
                    name = unicode(name.decode('utf-8'))

                if name.lower() in password.lower():
                    return _(u'Your password cannot contain your account name'
                             u'(Username), first name or last name.')

        # Checking if the entered password is different than already set
        # for this existing user
        if data.get('prevhash'):
            if AuthEncoding.pw_validate(data.get('prevhash'),
                                        password.encode('utf-8')):
                return _(u'You have to change your password.')

        # Checking it the entered password fits to the password policy scheme:
        # it must contain at least 3 from the 4 parts:
        # - Uppercase characters (A through Z)
        # - Lowercase characters (a through z)
        # - Numerals (0 through 9)
        # - Special characters such as !, $, #, %
        matches = 0
        if re.match(r'(?=.*[A-Z])', password):
            matches += 1
        if re.match(r'(?=.*[a-z])', password):
            matches += 1
        if re.match(r'(?=.*[0-9])', password):
            matches += 1
        if re.match(r'(?=.*[!$# %])', password):
            matches += 1
        if matches < 3:
            return _(u'Passwords must contain at least three of the following '
                     u'four character groups: '
                     u'Uppercase characters (A through Z), '
                     u'Lowercase characters (a through z), '
                     u'Numerals (0 through 9), '
                     u'Special characters such as !, $, #, %')

        return None
