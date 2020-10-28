from castle.cms.cdn import CDN
from castle.cms.interfaces import ICastleApplication
from plone import api
from Products.Five import BrowserView
from zope.component.interfaces import ComponentLookupError


class ErrorView(BrowserView):

    @property
    def is_zope_root(self):
        return ICastleApplication.providedBy(self.context)

    @property
    def logged_in(self):
        try:
            return not api.user.is_anonymous()
        except Exception:
            return False

    def format_error_message(self):
        return repr(self.context)

    def __call__(self):
        return self.index()

    def cdn_url(self, resource_type):
        try:
            cdn_url_tool = CDN(self.request.URL)
            options = cdn_url_tool.configured_resources
            if options[resource_type]:
                return cdn_url_tool.process_url(self.request.URL)
        except ComponentLookupError:
            return None
