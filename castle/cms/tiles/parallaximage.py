from castle.cms import defaults
from castle.cms.tiles.base import ContentTile
from castle.cms.tiles.image import ImageTile
from castle.cms.tiles.image import IImageTileSchema
from castle.cms.tiles.base import DisplayTypeTileMixin
from castle.cms.tiles.content import IImagesTileSchema
from castle.cms.tiles.views import BaseTileView
from castle.cms.tiles.views import TileViewsSource
from castle.cms.widgets import PreviewSelectFieldWidget
from plone.autoform import directives as form
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary

from zope.schema.vocabulary import SimpleTerm



class DefaultParallaxView(BaseTileView):
    name = 'default_parallax_image'
    order = 0
    index = ViewPageTemplateFile('templates/parallaximage.pt')
    tile_name = 'parallax_image'


class ParallaxImageTile(ImageTile):
    # display_type_name = 'parallax_image'
    # display_type_default = 'default_parallax_image'
    # display_type_fallback_view = DefaultParallaxView

    # render = DisplayTypeTileMixin.render_display
    index = ViewPageTemplateFile('templates/parallaximage.pt')

    pass


class IParallaxImageTileSchema(IImageTileSchema):

    # form.widget('display_type', PreviewSelectFieldWidget,
    #             tile_name='gallery')
    translate_z = schema.Int(
        title=u'Z-axis Setback',
        description=(
            u'How far behind the rest of the page the image appears to be. '
            u'The smaller the number, the slower the image content will appear to move. '
            u'Values can range from -100 to 2.'
        ),
        required=True,
        default=-1,
        max=2,
        min=-100,
    )

    height_percentage = schema.Int(
        title=u'Height percentage of orignal image',
        description=u'What percentage of the image\'s height will the parallax tile take uo.',
        required=True,
        default=100,
        max=200,
        min=1, 
    )

    heading_text = schema.TextLine(
        title=u'heading text',
        description=u'',
        required=False,
    )

    heading_size = schema.TextLine(
        title=u'heading size',
        description=u'',
        required=False,
    )
    body_text = schema.TextLine(
        title=u'body text',
        description=u'',
        required=False,
    )

    body_size = schema.TextLine(
        title=u'body size',
        description=u'',
        required=False,
    )

    text_position = schema.Choice(
        title=u'Image display type',
        description=u'Does not apply to all display types',
        default='n/a',
        required=False,
        vocabulary=SimpleVocabulary([
            SimpleTerm('n/a', 'n/a', u'N/A'),
            SimpleTerm('upper_left', 'upper_left', u'Upper Left'),
            SimpleTerm('upper_center', 'upper_center', u'Upper center'),
            SimpleTerm('upper_right', 'upper_right', u'Upper right'),
            SimpleTerm('middle_left', 'middle_left', u'Middle Left'),
            SimpleTerm('middle_center', 'middle_center', u'Middle center'),
            SimpleTerm('middle_right', 'middle_right', u'Middle right'),
            SimpleTerm('lower_left', 'lower_left', u'Lower Left'),
            SimpleTerm('lower_center', 'lower_center', u'Lower center'),
            SimpleTerm('lower_right', 'lower_right', u'Lower right'),
        ])
    )
