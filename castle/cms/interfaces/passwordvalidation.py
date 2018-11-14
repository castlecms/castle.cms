# -*- coding: utf-8 -*-

from zope.component.interfaces import IObjectEvent
from zope.interface import Attribute, Interface


class ICustomPasswordValidator(Interface):
    """
    Defines custom validators for the password
    chosen by the users.
    """

    def validate(password):
        """
        Validates password
        """


class IValidPasswordEntered(IObjectEvent):
    """
    """


class IInvalidPasswordEntered(IObjectEvent):
    """
    """


class IUserUnlocked(Interface):
    """
    """


user = Attribute("The user that was unlocked")
