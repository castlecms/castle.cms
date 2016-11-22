from castle.cms.tiles.base import BaseImagesTile
from castle.cms.tiles.views import BaseTileView
from castle.cms.tiles.views import getTileView
from castle.cms.tiles.views import TileViewsSource
from castle.cms.widgets import ImageRelatedItemsFieldWidget
from castle.cms.widgets import PreviewSelectFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import schema


class GalleryTile(BaseImagesTile):

    def render(self):
        view = getTileView(self.context, self.request, 'gallery',
                           self.data.get('display_type', 'default') or 'default',
                           default='default')
        if view is None:
            view = DefaultView(self.context, self.request)

        view.tile = self
        return view()


class IGalleryTileSchema(model.Schema):

    form.widget('images', ImageRelatedItemsFieldWidget)
    images = schema.List(
        title=u"Images",
        description=u"Select images or folders of images to display in "
                    u"gallery",
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    form.widget('display_type', PreviewSelectFieldWidget,
                tile_name='gallery')
    display_type = schema.Choice(
        title=u"Display Type",
        source=TileViewsSource('gallery'),
        default='default'
    )


class DefaultView(BaseTileView):
    name = 'default'
    order = 0
    index = ViewPageTemplateFile('templates/gallery/default.pt')
    tile_name = 'gallery'
