from castle.cms.theming import contentpanel_xpath
from lxml.html import tostring
from plone.app.blocks import gridsystem
from plone.app.blocks import tiles
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.utils import getLayout
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from Products.CMFPlone.browser.syndication import adapters
from Products.CMFPlone.interfaces.syndication import IFeed
from repoze.xmliter.utils import getHTMLSerializer
from zope.component import adapts
from zope.component import getAdapters
from zope.globalrequest import getRequest


class LayoutAwareItem(adapters.DexterityItem):
    adapts(ILayoutAware, IFeed)

    def render_content_core(self):
        try:
            layout = getLayout(self.context)
        except TypeError:
            return super(LayoutAwareItem, self).render_content_core()
        req = getRequest()
        filters = [f for _, f
                   in getAdapters((self.context, req), IFilter)]
        layout = apply_filters(filters, layout)
        dom = getHTMLSerializer(layout)
        tiles.renderTiles(req, dom.tree, self.context.absolute_url() + '/layout_view')
        gridsystem.merge(req, dom.tree)

        content = contentpanel_xpath(dom.tree)
        if len(content) > 0:
            return tostring(content[0])
        return ''
