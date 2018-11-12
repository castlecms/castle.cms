from castle.cms.interfaces.passwordvalidation import ICustomPasswordValidator
from plone import api
from zope.interface import implementer

from castle.cms import _


@implementer(ICustomPasswordValidator)
class EightCharMin(object):
    """ Checks if the password has already been used
    by iterating over the memberdata property password_history_size.
    """

    def __init__(self, context):
        self.context = context

    def validate(self, password, data):
        # Permit empty passwords here to allow registration links.
        # Plone will force the user to set one.
        if password is None:
            return None

        if api.user.is_anonymous():
            # No check for registrations.
            return None

        if len(password) < 8:
            return _(
                u'Minimum 8 characters',
                default=u'Minimum 8 characters'
            )
        return None
