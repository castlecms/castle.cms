from castle.cms.theming import contentpanel_xpath
from castle.cms.utils import has_image
from lxml.html import tostring
from plone.app.blocks import gridsystem
from plone.app.blocks import tiles
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.utils import getLayout
from plone.namedfile.interfaces import INamedField
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from plone.rfc822.interfaces import IPrimaryFieldInfo
from Products.CMFPlone.browser.syndication import adapters
from Products.CMFPlone.interfaces.syndication import IFeed
from repoze.xmliter.utils import getHTMLSerializer
from ZODB.POSException import POSKeyError
from zope.component import adapts
from zope.component import getAdapters
from zope.globalrequest import getRequest


class DexterityItem(adapters.DexterityItem):
    image = None
    file = None

    def __init__(self, context, feed):
        self.context = context
        self.feed = feed
        try:
            self._init()
        except (POSKeyError, AttributeError, TypeError):
            pass

    def _init(self):
        """
        moved here just so we can wrap it in exception block more nicely
        """

        if has_image(self.context):
            self.image = self.context.image
            self.field_name = 'image'

        try:
            primary = IPrimaryFieldInfo(self.context, None)
            if (INamedField.providedBy(primary.field) and
                    hasattr(primary.value, 'getSize') and
                    primary.value.getSize() > 0):
                self.file = primary.value
                self.field_name = primary.fieldname
        except TypeError:
            pass

    @property
    def file_length(self):
        if self.has_enclosure:
            try:
                return self.file.getSize()
            except POSKeyError:
                pass
            except SystemError:
                pass
        return 0

    @property
    def has_image(self):
        return self.image is not None

    @property
    def image_url(self):
        if self.image:
            return '{}/@@images/image'.format(self.base_url)

    @property
    def image_type(self):
        if self.image:
            return self.image.contentType


class LayoutAwareItem(DexterityItem):
    adapts(ILayoutAware, IFeed)

    def render_content_core(self, site=None):
        try:
            layout = getLayout(self.context)
        except TypeError:
            return super(LayoutAwareItem, self).render_content_core()
        req = getRequest()
        filters = [f for _, f
                   in getAdapters((self.context, req), IFilter)]
        layout = apply_filters(filters, layout)
        dom = getHTMLSerializer(layout)

        kwargs = {
            'baseURL': self.context.absolute_url() + '/layout_view'
        }
        if site is not None:
            kwargs['site'] = site

        tiles.renderTiles(req, dom.tree, **kwargs)
        gridsystem.merge(req, dom.tree)

        content = contentpanel_xpath(dom.tree)
        if len(content) > 0:
            return tostring(content[0])
        return ''
