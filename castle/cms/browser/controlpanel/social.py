# -*- coding: utf-8 -*-
from castle.cms.services import twitter
from castle.cms.interfaces import ISocialMediaSchema
from plone import api
from plone.app.registry.browser import controlpanel
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.interfaces import HIDDEN_MODE
from zope.component import getUtility
from zope.interface import alsoProvides


class AuthorizeTwitter(BrowserView):

    def __call__(self):
        if 'oauth_verifier' in self.request.form:
            alsoProvides(self.request, IDisableCSRFProtection)
            tokens = twitter.authorize()
            registry = getUtility(IRegistry)
            registry['plone.twitter_oauth_token'] = tokens['oauth_token']
            registry['plone.twitter_oauth_secret'] = tokens['oauth_token_secret']
            registry['plone.twitter_screen_name'] = tokens['screen_name']
            self.request.response.redirect('%s/@@social-controlpanel' % (
                api.portal.get().absolute_url()))
        else:
            self.request.response.redirect(twitter.get_auth_url())


class SocialControlPanelForm(controlpanel.RegistryEditForm):

    id = "SocialControlPanel"
    label = _(u"Social Media Settings")
    description = _("Social media sharing settings.")
    schema = ISocialMediaSchema
    schema_prefix = "plone"

    def updateWidgets(self):
        super(SocialControlPanelForm, self).updateWidgets()
        self.widgets["twitter_oauth_token"].mode = HIDDEN_MODE
        self.widgets["twitter_oauth_secret"].mode = HIDDEN_MODE
        self.widgets["twitter_screen_name"].mode = HIDDEN_MODE


class SocialControlPanel(controlpanel.ControlPanelFormWrapper):
    form = SocialControlPanelForm

    index = ViewPageTemplateFile('templates/social.pt')

    def hasTwitterApp(self):
        keys = twitter.get_keys()
        if keys[0] is None or keys[1] is None:
            return False
        return True

    def hasTwitterUserAuth(self):
        return twitter.get_auth() is not None
