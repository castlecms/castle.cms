# -*- coding: utf-8 -*-

from castle.cms.pwexpiry.interfaces import (IInvalidPasswordEntered,
                                            IUserUnlocked,
                                            IValidPasswordEntered)
from zope.component.interfaces import ObjectEvent
from zope.interface import implements


class ValidPasswordEntered(ObjectEvent):
    """A user enetered a valid password
    """
    implements(IValidPasswordEntered)


class InvalidPasswordEntered(ObjectEvent):
    """A user enetered an invalid password
    """
    implements(IInvalidPasswordEntered)


class UserUnlocked(object):
    """An user has been unlocked from the control panel tool
    """
    implements(IUserUnlocked)

    def __init__(self, user):
        self.user = user
