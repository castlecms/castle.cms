from castle.cms.interfaces import IVersionViewLayer
from DateTime import DateTime
from lxml.html import fromstring
from lxml.html import tostring
from plone import api
from plone.app.layout.viewlets.content import ContentHistoryView as BaseContentHistoryView
from plone.app.layout.viewlets.content import HistoryByLineView
from plone.memoize.view import memoize
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFEditions.browser.diff import DiffView
from Products.CMFPlone.browser.syndication.adapters import SearchFeed
from Products.CMFPlone.interfaces.syndication import IFeedItem
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryMultiAdapter
from zope.interface import alsoProvides
from zope.interface import noLongerProvides


class HistoryView(HistoryByLineView):
    index = ViewPageTemplateFile('templates/history_view.pt')

    def show(self):
        """
        just use permission checking
        """
        return True

    def show_history(self):
        """
        see comment for pervious method
        """
        return True


class ContentHistoryView(BaseContentHistoryView):
    index = ViewPageTemplateFile("templates/content_history.pt")


class HistoryVersionView(DiffView):
    template = ViewPageTemplateFile("templates/history_version.pt")

    def getContent(self, version):
        alsoProvides(self.request, IVersionViewLayer)
        feed = SearchFeed(api.portal.get())
        adapter = queryMultiAdapter((version, feed), IFeedItem)
        content = adapter.render_content_core().strip()
        noLongerProvides(self.request, IVersionViewLayer)

        if not content:
            # try old fashioned way... bah!
            content = version.restrictedTraverse(version.defaultView())()
            dom = fromstring(content)
            return ''.join([tostring(el) for el in dom.cssselect('#content-core > *')])
        else:
            dom = fromstring(content)
            return ''.join([tostring(el) for el in dom.cssselect('[data-panel] > *')])

    @property
    @memoize
    def versions(self):
        version_history = []
        rt = api.portal.get_tool("portal_repository")
        history = rt.getHistoryMetadata(self.context)
        retrieve = history.retrieve
        getId = history.getVersionId

        # Count backwards from most recent to least recent
        for i in xrange(history.getLength(countPurged=False) - 1, -1, -1):
            version_id = getId(i, countPurged=False)
            data = retrieve(i, countPurged=False)
            meta = data["metadata"]["sys_metadata"]
            version_history.append({
                'dt': DateTime(meta['timestamp']),
                'comments': meta['comment'],
                'version_id': version_id
            })

        return version_history

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        self.version_info = None
        for version in self.versions:
            if str(version['version_id']) == self.request.form.get('version'):
                self.version_info = version
        return self.template()
