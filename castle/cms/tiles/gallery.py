from castle.cms import defaults
from castle.cms.tiles.base import BaseImagesTile
from castle.cms.tiles.base import DisplayTypeTileMixin
from castle.cms.tiles.content import IImagesTileSchema
from castle.cms.tiles.views import BaseTileView
from castle.cms.tiles.views import TileViewsSource
from castle.cms.widgets import PreviewSelectFieldWidget
from plone.autoform import directives as form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
import zope.schema as schema
from zope.schema.vocabulary import SimpleVocabulary


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

    @property
    def gallery_height(self):
        return (self.data or {}).get('gallery_height', 'default')


class IGalleryTileSchema(IImagesTileSchema):

    form.widget('display_type', PreviewSelectFieldWidget,
                tile_name='gallery')
    display_type = schema.Choice(
        title=u"Display Type",
        source=TileViewsSource('gallery'),
        default=defaults.get('gallery_tile_displaytype', u'default')
    )

    gallery_height = schema.Choice(
        title=u"Gallery Height",
        default='default',
        vocabulary=SimpleVocabulary([
            SimpleVocabulary.createTerm('small', 'small', 'Small'),
            SimpleVocabulary.createTerm('default', 'default', 'Default'),
            SimpleVocabulary.createTerm('large', 'large', 'Large'),
            SimpleVocabulary.createTerm('x-large', 'x-large', 'X-Large')
        ])
    )

    show_thumbnails = schema.Bool(
        title=u'Show Thumbnails',
        description=(
            u'Display thumbnail images below main gallery image. '
            u'This option is for advanced display types in certain \
                add-ons.Usually, this option has no affect.'
        ),
        missing_value=True,
        required=False,
    )

    show_image_title = schema.Bool(
        title=u'Show Image Title',
        description=(
            u'Display Image Title directly below the main gallery image. '
            u'This option is for advanced display types in certain add-ons. \
                Usually, this option has no affect.'
        ),
        missing_value=True,
        required=False,
    )

    show_image_captions = schema.Bool(
        title=u'Show Image Captions',
        description=(
            u'Display a small caption (the image\'s summary field) below either \
                the image title (if visible) or the main image. '
            u'This option is for advanced display types in certain add-ons. \
                Usually, this option has no affect.'
        ),
        missing_value=True,
        required=False,
    )

    show_image_counter = schema.Bool(
        title=u'Show Image Counter',
        description=(
            u'Display a small indicator above the main image indicating which \
                image is being viewed (ex: "Image 15 of 22"). '
            u'This option is for advanced display types in certain add-ons. \
                Usually, this option has no affect.'
        ),
        missing_value=False,
        required=False,
    )

    show_link_to_original_image = schema.Bool(
        title=u'Show Link to Original Image',
        description=(
            u'When the gallery image is highlighted, show a link to the original image. '
            u'This option is for advanced display types in certain add-ons. Usually, \
                this option has no affect.'
        ),
        missing_value=False,
        required=False,
    )

    # use_custom_image_captions = schema.Bool(
    #     title=u'Use Custom Image Captions',
    #     description=(
    #         u'The default behavior when Image Captions are enabled is to use the summary '
    #         u'contained on each image item as the caption. This option allows a custom '
    #         u'caption to be specified for each image above.'
    #     ),
    #     missing_value=False,
    #     required=False,
    # )
