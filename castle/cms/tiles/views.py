from Acquisition import aq_parent
from castle.cms.interfaces import ITileView
from castle.cms.behaviors.adjustablefont import IAdjustableFontSizeQueryListing
from castle.cms.behaviors.adjustablefont import get_inline_style
from plone.dexterity.interfaces import IDexterityContent
from Products.Five import BrowserView
from zope.component import getAdapters
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def getTileViews(context, request, tile_name):
    adapters = getAdapters((context, request), ITileView)
    views = []
    for _, adapter in adapters:
        if adapter.tile_name == tile_name:
            views.append(adapter)
    return list(sorted(views, key=lambda x: x.order))


def getTileView(context, request, tile_name, view_name, default=None):
    for View in getTileViews(context, request, tile_name):
        if View.name == view_name:
            return View
    # use default maybe..
    if default is not None:
        return getTileView(context, request, tile_name, default)


@implementer(ITileView)
class BaseTileView(BrowserView):
    order = 0
    name = None
    tile_name = None
    label = None
    preview = None
    hidden = False
    font_sizes = {}
    adjustable_font_behaviors = [
        {
            'interface': IAdjustableFontSizeQueryListing,
            'tile_type': 'query_listing',
        }
    ]

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.tile = None

    def __call__(self):
        for behavior in self.adjustable_font_behaviors:
            if behavior['interface'].providedBy(self.context):
                self.font_sizes[behavior['tile_type']] = get_inline_style(self.context, behavior['tile_type'])
        return self.index()


@implementer(IContextSourceBinder)
class TileViewsSource(object):

    def __init__(self, tile_name):
        self.tile_name = tile_name

    def __call__(self, context):
        terms = []
        if not IDexterityContent.providedBy(context):
            context = aq_parent(context)
        for View in getTileViews(context, getRequest(), self.tile_name):
            if View.hidden:
                continue
            label = View.label
            if label is None:
                label = View.name.capitalize()
            terms.append(SimpleTerm(View.name, View.name, label))
        return SimpleVocabulary(terms)
