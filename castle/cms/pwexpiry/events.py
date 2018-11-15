# -*- coding: utf-8 -*-

from castle.cms.interfaces.passwordvalidation import (IInvalidPasswordEntered,
                                                      IUserUnlocked,
                                                      IValidPasswordEntered)
from zope.component.interfaces import ObjectEvent
from zope.interface import implements


class ValidPasswordEntered(ObjectEvent):
    """A user entered a valid password
    """
    implements(IValidPasswordEntered)


class InvalidPasswordEntered(ObjectEvent):
    """A user entered an invalid password
    """
    implements(IInvalidPasswordEntered)


class UserUnlocked(object):
    """A user has been unlocked from the control panel tool
    """
    implements(IUserUnlocked)

    def __init__(self, user):
        self.user = user
