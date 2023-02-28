# -*- coding: utf-8 -*-

from zope.component.interfaces import ObjectEvent
from zope.interface import implementer

from castle.cms.interfaces.passwordvalidation import IInvalidPasswordEntered
from castle.cms.interfaces.passwordvalidation import IUserUnlocked
from castle.cms.interfaces.passwordvalidation import IValidPasswordEntered


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

    def __init__(self, user):
        self.user = user
