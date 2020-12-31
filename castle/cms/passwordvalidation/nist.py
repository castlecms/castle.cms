from castle.cms.interfaces.passwordvalidation import ICustomPasswordValidator
from castle.cms.pwexpiry.password_history_validator import PasswordHistoryValidator
from plone import api
from plone.api.portal import get_registry_record as get_rec
from zope.interface import implementer

from castle.cms.pwexpiry.config import _

import re


@implementer(ICustomPasswordValidator)
class NISTPasswordValidator(object):

    def __init__(self, password):
        self.password = password
        self.props = {}
        default_props = {'length': 12, 'uppercase': 1, 'lowercase': 1, 'special': 1}

        # Sets the properties from control panel if specified or defaults if not
        for key in default_props:
            if get_rec('plone.nist_require_password_%s' % key):
                self.props[key] = get_rec('plone.nist_minimum_password_%s' % key)
            else:
                self.props[key] = default_props[key]

    def validate(self, password, data=None):
        #! PROBABLY DELETE!!!
        # if check_history:
        #     user = api.user.get_current()
        #     password_history = PasswordHistoryValidator(self)
        #     reused_password = password_history.validate(self.password, user)

        #     if reused_password:
        #         raise NISTError('Password has been used previously, please create a unique password.',
        #                         'history')

        self.password = password
        for prop in self.props:
            if prop == 'length':
                required_length = self.props[prop]
                actual_length = len(self.password)
                if actual_length < required_length:
                    return _('Password must be at least %s character(s) long.' % required_length)
            elif prop == 'uppercase':
                required_uppercase = self.props[prop]
                actual_uppercase = sum(1 for c in self.password if c.isupper())
                if actual_uppercase < required_uppercase:
                    return _('Password must contain at least %s uppercase character(s).' % required_uppercase)
            elif prop == 'lowercase':
                required_lowercase = self.props[prop]
                actual_lowercase = sum(1 for c in self.password if c.islower())
                if actual_lowercase < required_lowercase:
                    return _('Password must contain at least %s lowercase character(s).' % required_lowercase)
            elif prop == 'special':
                required_special = self.props[prop]
                regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
                actual_special = len(re.findall(regex, self.password))
                if actual_special < required_special:
                    return _('Password must contain at least %s special character(s).' % required_special)


#! PROBABLY DELETE!!!
class NISTError(Exception):
    def __init__(self, msg, prop):
        self.msg = msg
        self.prop = prop
