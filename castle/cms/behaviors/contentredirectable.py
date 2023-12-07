# -*- coding: utf-8 -*-
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.app.contenttypes.utils import replace_link_variables_by_paths
from plone.dexterity.interfaces import IDexterityContent
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer
from zope.interface import provider
from zope.globalrequest import getRequest

import zope.schema as schema
import plone.api as api


class IContentRedirectableMarker(Interface):
    pass


@provider(IFormFieldProvider)
class IContentRedirectable(model.Schema):

    model.fieldset(
        'settings',
        label=u'Settings',
        fields=[
            'enable_redirect',
            'redirect_url',
        ],
    )

    directives.write_permission(enable_redirect='cmf.ModifyPortalContent')
    enable_redirect = schema.Bool(
        title=u'Enable Redirect',
        description=(
            u'If checked, non-editors will be redirected to "Redirect URL" below '
            u'when attempting to navigate to this content. '
            u'(If no value is provided for "Redirect URL", no redirect will occur)'
        ),
        required=False,
    )

    directives.write_permission(redirect_url='cmf.ModifyPortalContent')
    redirect_url = schema.TextLine(
        title=u'Redirect URL',
        description=(
            u'If "Enable Redirect" is checked above, a redirect will be performed when a '
            u'non-editor attempts to navigate to this content. '
            u'The link is used almost verbatim, relative links become absolute and the strings '
            u'"${navigation_root_url}" and "${portal_url}" get replaced with the real navigation_root_url or portal_url. '
            u'If in doubt which one to use, please use navigation_root_url.'
        ),
        required=False,
    )

@implementer(IContentRedirectable)
@adapter(IDexterityContent)
class ContentRedirectable(object):

    @property
    def non_redirectable_url_schemes(self):
        return [ 'mailto:', 'tel:', 'callto:', 'webdav:', 'caldav:' ]

    @property
    def non_resolvable_url_schemes(self):
        return self.non_redirectable_url_schemes + ['file:', 'ftp:']

    def __init__(self, context, request=None):
        self.context = context
        self.request = request or getRequest()

    @property
    def enable_redirect(self):
        return getattr(self.context, 'enable_redirect', False)

    @enable_redirect.setter
    def enable_redirect(self, value):
        setattr(self.context, 'enable_redirect', value)

    @enable_redirect.deleter
    def enable_redirect(self, value):
        delattr(self.context, 'enable_redirect')

    @property
    def redirect_url(self):
        return getattr(self.context, 'redirect_url', None)

    @redirect_url.setter
    def redirect_url(self, value):
        setattr(self.context, 'redirect_url', value)

    @redirect_url.deleter
    def redirect_url(self, value):
        delattr(self.context, 'redirect_url')

    @property
    def is_redirect_configured(self):
        return (
            self.enable_redirect is True and
            bool(self.redirect_url) is True
        )

    @property
    def user_can_edit(self):
        membership_tool = api.portal.get_tool('portal_membership')
        return membership_tool.checkPermission('Modify portal content', self.context)

    @property
    def is_redirectable(self):
        return (
            self.is_redirect_configured
            and not self._url_uses_scheme(self.non_redirectable_url_schemes)
        )

    @property
    def should_redirect(self):
        return self.is_redirectable and not self.user_can_edit

    # the methods below are adapted from plone.app.contenttypes.browser.link_redirect_view.LinkRedirectView
    @property
    def formatted_redirect_url(self):
        return replace_link_variables_by_paths(self.context, self.redirect_url)

    def _url_uses_scheme(self, schemes):
        url = self.formatted_redirect_url
        for scheme in schemes:
            if type(url) is str and url.startswith(scheme):
                return True
        return False

    def attempt_redirect(self):
        """Redirect to the redirect_url, if and only if:
         - is_redirect_configured property returns True
         - the link is of a redirectable type (no mailto:, etc)
         - AND current user doesn't have permission to edit the Content Object"""

        if self.is_redirectable:
            url = self.absolute_target_url()
            if not url:
                return
            if self.user_can_edit:
                message = (
                    'This object is currently configured to redirect to {}. '.format(url) +
                    'You are able to see this view because you have permission to edit this object.'
                )
                api.portal.show_message(
                    message,
                    request=self.request,
                    type='warning',
                )
            else:
                return self.request.response.redirect(url.encode('utf-8'))

    def absolute_target_url(self):
        """Compute the absolute target URL."""
        url = self.redirect_url
        if not url:
            return

        if self._url_uses_scheme(self.non_resolvable_url_schemes):
            # For non http/https url schemes, there is no path to resolve.
            return url

        if url.startswith('.'):
            # we just need to adapt ../relative/links, /absolute/ones work
            # anyway -> this requires relative links to start with ./ or
            # ../
            context_state = self.context.restrictedTraverse( '@@plone_context_state' )
            return context_state.canonical_object_url() + '/' + url
        else:
            url = replace_link_variables_by_paths(self.context, url)
            if not url.startswith(('http://', 'https://')):
                url = self.request.physicalPathToURL(url)

        return url
