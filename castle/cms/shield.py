from castle.cms.interfaces import ISecureLoginAllowedView
from plone import api
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import queryUtility
from castle.cms import constants


SHIELD = constants.SHIELD

_blacklisted_meta_types = (
    'Image', 'File', 'Filesystem Image',
    'Filesystem File', 'Stylesheets Registry', 'JavaScripts Registry',
    'DirectoryViewSurrogate', 'KSS Registry', 'Filesystem Directory View')


def protect(req):
    published = req.PARENTS[0]
    mt = getattr(
        getattr(published, 'aq_base', None),
        'meta_type',
        getattr(published, 'meta_type', None))
    if mt in _blacklisted_meta_types or mt is None:
        return

    published = req.get('PUBLISHED')
    if ISecureLoginAllowedView.providedBy(published):
        return

    registry = queryUtility(IRegistry)
    setting = (registry and
               registry.get('plone.login_shield_setting', SHIELD.NONE) or
               SHIELD.NONE)

    protect = False
    if setting == SHIELD.ALL:
        protect = True
    elif setting == SHIELD.BACKEND:
        backend_url = (registry and
                       registry.get('plone.backend_url', SHIELD.NONE) or
                       '')
        if backend_url.startswith(req.SERVER_URL):
            protect = True
    if protect and api.user.is_anonymous():
        raise Redirect('{}/@@secure-login'.format(
            api.portal.get().absolute_url()))
