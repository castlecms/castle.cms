# -*- coding: utf-8 -*-
import json

from castle.cms.interfaces import ISocialMediaSchema
from castle.cms.services.google import GOOGLE_CLIENT_ID
from castle.cms.services.google import GOOGLE_CLIENT_SECRET
from castle.cms.services import twitter
from castle.cms.services.google import youtube
from oauth2client.client import OAuth2WebServerFlow
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


class AuthorizeGoogle(BrowserView):

    def __call__(self):
        client = OAuth2WebServerFlow(
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scope=youtube.SCOPES,
            redirect_uri='{}/@@google-auth'.format(
                self.context.absolute_url()))
        if 'code' in self.request.form:
            creds = client.step2_exchange(self.request.form['code'])
            alsoProvides(self.request, IDisableCSRFProtection)
            registry = getUtility(IRegistry)
            registry['plone.google_oauth_token'] = json.dumps(
                creds.token_response).decode('utf-8')
            self.request.response.redirect('%s/@@social-controlpanel' % (
                api.portal.get().absolute_url()))
        else:
            self.request.response.redirect(
                client.step1_get_authorize_url())


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
        self.widgets["google_oauth_token"].mode = HIDDEN_MODE


class SocialControlPanel(controlpanel.ControlPanelFormWrapper):
    form = SocialControlPanelForm

    index = ViewPageTemplateFile('templates/social.pt')

    def get_auths(self):
        keys = twitter.get_keys()
        registry = getUtility(IRegistry)
        google_auth = True
        check_keys = ('plone.google_oauth_token',)
        for key in check_keys:
            if not registry.get(key, None):
                google_auth = False

        return {
            'twitter': {
                'client': keys[0] is not None and keys[1] is not None,
                'authorized': twitter.get_auth() is not None
            },
            'google': {
                'client': (GOOGLE_CLIENT_ID is not None and
                           GOOGLE_CLIENT_SECRET is not None),
                'authorized': google_auth
            }
        }
