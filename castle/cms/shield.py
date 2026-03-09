from Acquisition import aq_parent
from castle.cms import constants
from castle.cms.interfaces import ISecureLoginAllowedView
from plone.registry.interfaces import IRegistry
from zExceptions import Redirect
from zope.component import queryUtility
import plone.api as api

SHIELD = constants.SHIELD

def protect(req, recheck=False):
    url = req.getURL()
    login_url = '{}/@@secure-login'.format(api.portal.get().absolute_url())
    if '@@secure-login' in url.lower() and url != login_url:
        raise Redirect(login_url)

    url = req.get('URL', None)
    whitelisted_requests = (
        'bootstrap.css',
        'secure-login.css',
        'secure-login.js',
        'require.js',
        'jquery.min.js',
        'bootstrap.min.js',
        'react.js',
        'utils.js',
        'favicon.ico',
    )

    if is_whitelisted(req, whitelisted_requests):
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


def is_whitelisted(request, whitelist):
    url = request.get('URL', None)
    if url is None:
        return False

    url_without_querys = url.split('?')[0]
    for resource in whitelist:
        if url_without_querys.endswith(resource):
            return True

    if '/@@site-logo' in url_without_querys:
        return True

    return False