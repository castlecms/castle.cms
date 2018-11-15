from AccessControl import AuthEncoding
from castle.cms.interfaces.passwordvalidation import ICustomPasswordValidator
from plone import api
from zope.interface import implementer

from .config import _


@implementer(ICustomPasswordValidator)
class PasswordHistoryValidator(object):
    """ Checks if the password has already been used
    by iterating over the memberdata property password_history_size.
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

        if api.user.is_anonymous():
            # No check for registrations.
            return None

        pwexpiry_enabled = api.portal.get_registry_record(
            'plone.pwexpiry_enabled'
        )
        max_history_pws = api.portal.get_registry_record(
            'plone.pwexpiry_password_history_size'
        )
        if max_history_pws == 0 or not pwexpiry_enabled:
            # max_history_pws has been disabled.
            return None

        user = api.user.get_current()

        # Ignore whitelisted
        whitelisted = api.portal.get_registry_record(
            'plone.pwexpiry_whitelisted_users'
        )
        if whitelisted and user.getId() in whitelisted:
            return None

        pw_history = user.getProperty('password_history', [])

        for old_pw in pw_history[-max_history_pws:]:
            if AuthEncoding.pw_validate(old_pw, str(password)):
                return _(
                    u'info_reused_pw',
                    default=u'This password has been used already.'
                )

        # All fine
        return None
