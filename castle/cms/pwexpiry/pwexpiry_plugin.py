# -*- coding: utf-8 -*-

from AccessControl import AuthEncoding, ClassSecurityInfo, Unauthorized
from castle.cms.pwexpiry.config import _
from castle.cms.pwexpiry.utils import days_since_event
from DateTime import DateTime
from Globals import InitializeClass
from plone import api
from plone.registry.interfaces import IRegistry
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PlonePAS.interfaces.plugins import IUserManagement
from Products.PluggableAuthService.interfaces.plugins import (IAuthenticationPlugin,
                                                              IChallengePlugin)
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.statusmessages.interfaces import IStatusMessage
from zope.component import getUtility
from zope.interface import implements

manage_addPwExpiryPluginForm = PageTemplateFile(
    'www/addPwExpiryPlugin',
    globals(), __name__='manage_addPwExpiryPlugin'
)

def addPwExpiryPlugin(self, id, title='', REQUEST=None):
    """
    Add PwExpiry plugin
    """
    o = PwExpiryPlugin(id, title)
    self._setObject(o.getId(), o)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(
            '%s/manage_main'
            '?manage_tabs_message=PwExpiry+Plugin+added.' %
            self.absolute_url()
        )


class PwExpiryPlugin(BasePlugin):
    """
    Password expiry plugin
    """
    meta_type = 'Password Expiry Plugin'
    security = ClassSecurityInfo()
    implements(IAuthenticationPlugin, IChallengePlugin, IUserManagement)

    def __init__(self, id, title=None):
        self._setId(id)
        self.title = title

    # IAuthenticationPlugin implementation
    security.declarePrivate('authenticateCredentials')

    def authenticateCredentials(self, credentials):
        """
        Check if the user.password_date is older than validity_period.
        If validity_period is 0, skip the check
        """
        login = credentials.get('login')
        if not login:
            return None

        self._invalidatePrincipalCache(login)
        user = api.user.get(username=login)
        if not user:
            return None

        registry = getUtility(IRegistry)
        pwexpiry_enabled = registry['plone.pwexpiry_enabled']
        validity_period = registry['plone.pwexpiry_validity_period']
        if validity_period == 0 or not pwexpiry_enabled:
            return None

        # Ignore whitelisted
        whitelisted = api.portal.get_registry_record(
            'plone.pwexpiry_whitelisted_users'
        )
        if user.getId() in whitelisted:
            return None

        password_date = user.getProperty('password_date', '2000/01/01')
        if str(password_date) != '2000/01/01':
            current_time = DateTime()
            since_last_pw_reset = days_since_event(password_date.asdatetime(),
                                                   current_time.asdatetime())
            # Password has expired
            if validity_period - since_last_pw_reset < 0:
                user.setMemberProperties({
                    'reset_password_required': True,
                    'reset_password_time': time.time()
                })
                self.REQUEST.RESPONSE.setHeader('user_expired', user.getId())
                raise Unauthorized
        else:
            editableUser.setMemberProperties({
                'password_date': current_time
            })
        return None

    # IChallengePlugin implementation
    security.declarePrivate('challenge')
    def challenge(self, request, response, **kw):
        """
        Challenge the user for credentials
        """
        user_expired = response.getHeader('user_expired')
        if user_expired:
            portal_url = api.portal.get_tool(name='portal_url')()
            IStatusMessage(request).add(
                _(u'Your password has expired.'), type='error'
            )
            response.redirect(
                '%s/mail_password_form?userid=%s' % (portal_url, user_expired),
                lock=1
            )
            return 1
        return 0

    # IUserManagement implementation
    security.declarePrivate('doChangeUser')
    def doChangeUser(self, principal_id, password):
        """
        Update user's password date and store passwords history.
        """
        user = api.user.get(username=principal_id)
        portal = api.portal.get()
        current_time = portal.ZopeTime()
        user.setMemberProperties({'password_date': current_time})
        self._invalidatePrincipalCache(principal_id)

        # Remember passwords here
        max_history_pws = api.portal.get_registry_record(
            'plone.pwexpiry_password_history_size'
        )

        if max_history_pws == 0:
            # disabled, return here.
            return

        enc_pw = password
        if not AuthEncoding.is_encrypted(enc_pw):
            enc_pw = AuthEncoding.pw_encrypt(enc_pw)

        pw_history = list(user.getProperty('password_history', []))
        pw_history.append(enc_pw)
        if len(pw_history) > max_history_pws:
            # Truncate the history
            pw_history = pw_history[-max_history_pws:]

        user.setMemberProperties({'password_history': pw_history})


InitializeClass(PwExpiryPlugin)
