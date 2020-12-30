from castle.cms.pwexpiry.password_history_validator import PasswordHistoryValidator
from plone import api
from plone.api.portal import get_registry_record as get_rec

import re


class NISTPasswordValidator():

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

    def validate(self, check_history=False):
        if check_history:
            user = api.user.get_current()
            password_history = PasswordHistoryValidator(self)
            reused_password = password_history.validate(self.password, user)

            if reused_password:
                raise NISTError('Password has been used previously, please create a unique password.',
                                'history')

        for prop in self.props:
            if prop == 'length':
                required_length = self.props[prop]
                actual_length = len(self.password)
                if actual_length < required_length:
                    raise NISTError('Password must be at least %s characters long.' % required_length, prop)
            elif prop == 'uppercase':
                required_uppercase = self.props[prop]
                actual_uppercase = sum(1 for c in self.password if c.isupper())
                if actual_uppercase < required_uppercase:
                    raise NISTError('Password must contain %s uppercase letters.' % required_uppercase, prop)
            elif prop == 'lowercase':
                required_lowercase = self.props[prop]
                actual_lowercase = sum(1 for c in self.password if c.islower())
                if actual_lowercase < required_lowercase:
                    raise NISTError('Password must contain %s lowercase letters.' % required_lowercase, prop)
            elif prop == 'special':
                required_special = self.props[prop]
                regex = re.compile('[@_!#$%^&*()<>?/\|}{~:]')
                actual_special = len(re.findall(regex, self.password))
                if actual_special < required_special:
                    raise NISTError('Password must contain %s special characters.' % required_special, prop)


class NISTError(Exception):
    def __init__(self, msg, prop):
        self.msg = msg
        self.prop = prop
