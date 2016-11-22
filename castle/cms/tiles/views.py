from Acquisition import aq_parent
from castle.cms.interfaces import ITileView
from plone.dexterity.interfaces import IDexterityContent
from Products.Five import BrowserView
from zope.component import getAdapters
from zope.globalrequest import getRequest
from zope.interface import implements
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


class BaseTileView(BrowserView):
    implements(ITileView)
    order = 0
    name = None
    tile_name = None
    label = None
    preview = None
    hidden = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.tile = None

    def __call__(self):
        return self.index()


class TileViewsSource(object):
    implements(IContextSourceBinder)

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
