from castle.cms import archival
from castle.cms.files import aws
from plone import api
from Products.Five import BrowserView
from zExceptions import Redirect
from zope.component import queryMultiAdapter


class NotFoundView(BrowserView):

    def __call__(self):
        self.notfound = self.context
        self.context = api.portal.get()
        archive_storage = archival.Storage(self.context)
        site_url = self.context.absolute_url()
        path = self.request.ACTUAL_URL[len(site_url):].rstrip('/')

        wants_view = False
        if path.endswith('/view'):
            wants_view = True
            path = path.rsplit('/view', 1)[0]

        new_url = None
        if path.startswith('/resolveuid'):
            uid = path.replace('/resolveuid/', '')
            try:
                new_url = archive_storage.get_archive_url_by_uid(uid)
            except:
                pass
        else:
            try:
                new_url = archive_storage.get_archive_url_by_path(path, wants_view)
            except:
                pass
        if new_url:
            # XXX need to force redirect this way since normal redirect
            # gets overridden with 404
            if self.request.environ.get('QUERY_STRING'):
                new_url += '?' + self.request.environ['QUERY_STRING']
            raise Redirect(aws.swap_url(new_url))

        # seems this overrides plone.app.redirector handler
        redirector = queryMultiAdapter((self.context, self.request),
                                       name=u'plone_redirector_view')
        if redirector:
            redirector.attempt_redirect()

        return self.index()
