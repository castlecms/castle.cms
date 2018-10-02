from castle.cms.interfaces import ICastleApplication
from plone import api
from Products.Five import BrowserView


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
