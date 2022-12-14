from castle.cms import constants
from castle.cms.interfaces import ISecureLoginAllowedView
from plone import api
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import queryUtility
from Acquisition import aq_parent

SHIELD = constants.SHIELD

_blacklisted_meta_types = (
    'Image', 'File', 'Filesystem Image',
    'Filesystem File', 'Stylesheets Registry', 'JavaScripts Registry',
    'DirectoryViewSurrogate', 'KSS Registry', 'Filesystem Directory View')


def protect(req, recheck=False):
    url = req.getURL()
    login_url = '{}/@@secure-login'.format(api.portal.get().absolute_url())
    if '@@secure-login' in url.lower() and url != login_url:
        raise Redirect(login_url)

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
        backend_urls = (registry and
                        registry.get('plone.backend_url', SHIELD.NONE) or
                        [])
        for backend_url in backend_urls or []:
            try:
                protect |= backend_url.startswith(req.SERVER_URL)
            except AttributeError:
                pass
    if protect:
        if req.getURL().lower().endswith("robots.txt"):
            return """User-agent: *
Disallow: /"""

        if recheck:
            portal = api.portal.get()
            site_plugin = portal.acl_users.session
            creds = site_plugin.extractCredentials(req)
            anonymous = not site_plugin.authenticateCredentials(creds)
            if anonymous:
                try:
                    app_plugin = aq_parent(portal).acl_users.session
                    anonymous = not app_plugin.authenticateCredentials(creds)
                except AttributeError:
                    anonymous = True
        else:
            anonymous = api.user.is_anonymous()

        if anonymous:
            raise Redirect(login_url)
