from plone import api
from Products.PluggableAuthService.PluggableAuthService import _noroles
from zope.security import checkPermission
from AccessControl.SecurityManagement import noSecurityManager


ORIGINAL_USER_KEY = 'castle.cms.original_user'
COOKIE_NAME = 'impersonate'


def PAS_validate(self, request, auth='', roles=_noroles):
    user = self._old_validate(request, auth, roles)
    if user is None:
        return

    if request.cookies.get(COOKIE_NAME):
        # check if user can manage portal
        replacement_user_id = request.cookies[COOKIE_NAME]

        if replacement_user_id != 'ANONYMOUS':
            # allow all users to impersonate anonymous users
            try:
                if not checkPermission('cmf.ManagePortal', api.portal.get()):
                    return user
            except api.exc.CannotGetPortalError:
                return user

        (accessed, container, name, value) = self._getObjectContext(
            request['PUBLISHED'], request)
        if replacement_user_id == 'ANONYMOUS':
            plugins = self._getOb('plugins')
            replacement_user = self._createAnonymousUser(plugins)
        else:
            replacement_user = api.user.get(replacement_user_id)
            if replacement_user is not None:
                replacement_user = replacement_user.getUser()
        noSecurityManager()
        if self._authorizeUser(replacement_user, accessed, container,
                               name, value, roles):
            request.environ[ORIGINAL_USER_KEY] = user
            # required to use __of__ so user is wrapped in correct aq context
            return replacement_user.__of__(self)
        else:
            # if user doesn't authenticate, return None
            return None

    return user
