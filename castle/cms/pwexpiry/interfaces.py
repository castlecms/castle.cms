# -*- coding: utf-8 -*-

from zope.component.interfaces import IObjectEvent
from zope.interface import Attribute, Interface


class IExpirationCheck(Interface):
    """
    Compares the number of days left to password expiration and
    defines a notification action that is triggered if the number
    of days before password expiration is is equal to one of the
    numbers defined in the 'notify_on' attribute.
    It can be used as plugin system, that allows registering the
    notification actions for the specified number of days
    before password expiration.
    """

    notify_on = Attribute(
        'notify_on',
        'The integer or tuple of integers defining the '
        'numbers of days when the notification_action '
        'will be triggered.'
    )

    def __call__(days_to_expire):
        """
        Returns True if the number of days left to password expiration
        is equal to the numbers specified days_to_expire attribute.
        """

    def notification_action(userdata, days_to_expire):
        """
        Performs notification action, ie sending notification email.
        Triggered only when the number of days to password expiration
        is equal to the number specified in the ExpirationCheck
        """


class ICustomPasswordValidator(Interface):
    """
    Enables to define custom validators for the password
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


class ICollectivePWExpiryLayer(Interface):
    """A layer specific to the castle.cms.pwexpiry package.
    """
