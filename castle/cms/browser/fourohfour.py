import logging

from plone import api
from plone.app.redirector.browser import FourOhFourView
from plone.app.redirector.interfaces import IRedirectionStorage
from zExceptions import Redirect
from zope.component import queryUtility
from six.moves import urllib
from six.moves.urllib.parse import quote
from six.moves.urllib.parse import unquote

from castle.cms import archival
from castle.cms import shield
from castle.cms.files import aws


logger = logging.getLogger('castle.cms')


class FourOhFour(FourOhFourView):

    def __call__(self):
        shield.protect(self.request, recheck=True)
        self.notfound = self.context
        self.context = api.portal.get()
        if '++' in self.request.URL:
            self.request.response.setStatus(404)
            try:
                return self.index()
            except Exception:
                logger.warn("Failed to render 404 template, had to return simple response")
                return "not found"

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
            except Exception:
                pass
        else:
            try:
                new_url = archive_storage.get_archive_url_by_path(path, wants_view)
            except Exception:
                pass
        if new_url:
            # XXX need to force redirect this way since normal redirect
            # gets overridden with 404
            if self.request.environ.get('QUERY_STRING'):
                new_url += '?' + self.request.environ['QUERY_STRING']
            raise Redirect(aws.swap_url(new_url))

        self.attempt_redirect()

        self.request.response.setStatus(404)
        return self.index()

    def attempt_redirect(self):
        url = self._url()
        if not url:
            return False

        try:
            old_path_elements = self.request.physicalPathFromURL(url)
        except ValueError:
            return False

        storage = queryUtility(IRedirectionStorage)
        if storage is None:
            return False

        old_path = '/'.join(old_path_elements)

        # First lets try with query string in cases or content migration

        new_path = None

        query_string = self.request.QUERY_STRING
        if query_string:
            new_path = storage.get("%s?%s" % (old_path, query_string))
            # if we matched on the query_string we don't want to include it
            # in redirect
            if new_path:
                query_string = ''

        if not new_path:
            new_path = storage.get(old_path)

        if not new_path:
            new_path = self.find_redirect_if_view(old_path_elements, storage)

        if not new_path:
            new_path = self.find_redirect_if_template(
                url,
                old_path_elements,
                storage)

        if not new_path:
            return False

        url = urllib.parse.urlsplit(new_path)
        if url.netloc:
            # External URL
            # avoid double quoting
            url_path = unquote(url.path)
            url_path = quote(url_path)
            url = urllib.parse.SplitResult(
                *(url[:2] + (url_path, ) + url[3:])).geturl()
        else:
            url = self.request.physicalPathToURL(new_path)

        # some analytics programs might use this info to track
        if query_string:
            url += "?" + query_string
        raise Redirect(url)
        return True
