import logging

from AccessControl import AuthEncoding
from castle.cms.pwexpiry.events import (InvalidPasswordEntered,
                                        ValidPasswordEntered)
from castle.cms.interfaces.passwordvalidation import ICustomPasswordValidator
from plone import api
from Products.CMFPlone.RegistrationTool import RegistrationTool
from Products.PluggableAuthService.plugins.ZODBUserManager import \
    ZODBUserManager
from zope.component import getAdapters
from zope.event import notify

from hashlib import sha1 as sha


logger = logging.getLogger(__file__)


original_testPasswordValidity = RegistrationTool.testPasswordValidity


def extended_testPasswordValidity(self, password, confirm=None, data=None):
    """
    Patching the standard Plone's testPasswordValidity method to
    enable registering a custom password validator.
    """
    validators = getAdapters((self,), ICustomPasswordValidator)
    for name, validator in validators:
        result = validator.validate(password, data)
        if result:
            return result

    original = original_testPasswordValidity(self, password, confirm)
    if original:
        return original

    return None


RegistrationTool.testPasswordValidity = extended_testPasswordValidity


logger.info(
    "Patching Products.CMFDefault.RegistrationTool.testPasswordValidity"
)

ZODBUserManager.original_authenticateCredentials = ZODBUserManager.authenticateCredentials


def authenticateCredentials(self, credentials):
    """ See IAuthenticationPlugin.

    o We expect the credentials to be those returned by
      ILoginPasswordExtractionPlugin.
    """
    login = credentials.get('login')
    password = credentials.get('password')

    if login is None or password is None:
        return None

    # Do we have a link between login and userid?  Do NOT fall
    # back to using the login as userid when there is no match, as
    # that gives a high chance of seeming to log in successfully,
    # but in reality failing.
    userid = self._login_to_userid.get(login)
    if userid is None:
        # Someone may be logging in with a userid instead of a
        # login name and the two are not the same.  We could try
        # turning those around, but really we should just fail.
        #
        # userid = login
        # login = self._userid_to_login.get(userid)
        # if login is None:
        #     return None
        return None

    reference = self._user_passwords.get(userid)

    if reference is None:
        return None

    is_authenticated = False
    if AuthEncoding.is_encrypted(reference):
        if AuthEncoding.pw_validate(reference, password):
            is_authenticated = True

    if not is_authenticated:
        # Support previous naive behavior
        digested = sha(password).hexdigest()

        if reference == digested:
            is_authenticated = True

    if is_authenticated:
        try:
            user = api.user.get(username=login)
        except Exception:
            return userid, login

        event = ValidPasswordEntered(user)
        notify(event)
        return userid, login
    else:
        try:
            user = api.user.get(username=login)
        except Exception:
            return None

        event = InvalidPasswordEntered(user)
        notify(event)
        return None


ZODBUserManager.authenticateCredentials = authenticateCredentials
logger.info("Patching Products.PluggableAuthService.plugins.ZODBUserManager."
            "ZODBUserManager.authenticateCredentials")
