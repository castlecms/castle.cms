# -*- coding: utf-8 -*-

from castle.cms.interfaces.passwordvalidation import (IInvalidPasswordEntered,
                                                      IUserUnlocked,
                                                      IValidPasswordEntered)
from zope.component.interfaces import ObjectEvent
from zope.interface import implementer


@implementer(IValidPasswordEntered)
class ValidPasswordEntered(ObjectEvent):
    """A user entered a valid password
    """
    pass


@implementer(IInvalidPasswordEntered)
class InvalidPasswordEntered(ObjectEvent):
    """A user entered an invalid password
    """
    pass


@implementer(IUserUnlocked)
class UserUnlocked(object):
    """A user has been unlocked from the control panel tool
    """
    pass

    def __init__(self, user):
        self.user = user
