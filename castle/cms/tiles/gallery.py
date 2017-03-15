from castle.cms.tiles.base import BaseImagesTile
from castle.cms.tiles.base import DisplayTypeTileMixin
from castle.cms.tiles.views import BaseTileView
from castle.cms.tiles.views import TileViewsSource
from castle.cms.widgets import ImageRelatedItemsFieldWidget
from castle.cms.widgets import PreviewSelectFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import schema


class DefaultView(BaseTileView):
    name = 'default'
    order = 0
    index = ViewPageTemplateFile('templates/gallery/default.pt')
    tile_name = 'gallery'


class GalleryTile(BaseImagesTile, DisplayTypeTileMixin):
    display_type_name = 'gallery'
    display_type_default = 'default'
    display_type_fallback_view = DefaultView

    render = DisplayTypeTileMixin.render_display


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
