from castle.cms.tiles.base import BaseTile
from castle.cms.widgets import ImageRelatedItemFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class ParallaxTile(BaseTile):

    @property
    def relatedItems(self):
        return self.context.relatedItems

    def get_image(self):
        image = self.data.get('image')
        if not image:
            return
        return self.utils.get_object(self.data['image'][0])


class IParallaxTileSchema(model.Schema):

    # --------------------- Parallax Tile ---------------------
    model.fieldset(
        'parallax_tile',
        label=u'Parallax Tile',
        fields=[
            'image',
            'bg_color',
            'title',
            'text',
            'text_color',
            'text_shadow',
            'hor_text_position',
        ]
    )

    form.widget(image=ImageRelatedItemFieldWidget)
    image = schema.List(
        title=u'Parallax Image',
        description=u'Image with scrolling parallax effect.',
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    bg_color = schema.Choice(
        title=u'Background Color',
        description=u'If no image selected, tile will be this color',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('black', 'black', u'Black'),
            SimpleTerm('white', 'white', u'White'),
        ]),
        default=u'white'
    )

    title = schema.TextLine(
        title=u'Slide Title',
        description=u'Will be omitted if blank',
        required=False,
        default=u'')

    text = schema.Text(
        title=u'Slide Text',
        description=u'Will be omitted if blank',
        required=False,
        default=u'')

    text_color = schema.Choice(
        title=u'Text Color',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('black', 'black', u'Black'),
            SimpleTerm('white', 'white', u'White'),
        ]),
        default=u'black'
    )

    text_shadow = schema.Choice(
        title=u'Text Shadow',
        description=u'Adds a shadow to the text over the image.',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('None', 'None', u'None'),
            SimpleTerm('black', 'black', u'Black'),
            SimpleTerm('white', 'white', u'White'),
        ]),
        default=u'None'
    )

    hor_text_position = schema.Choice(
        title=u'Slide Text Position (Horizontal)',
        description=u'How the text will be horizontally positioned on the tile.',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('start', 'start', u'Left (Half Width)'),
            SimpleTerm('center', 'center', u'Center (Full Width)'),
            SimpleTerm('end', 'end', u'Right (Half Width)'),
        ]),
        default=u'center'
    )

    # --------------------- Static Tile ---------------------
    model.fieldset(
        'static_tile',
        label=u'Static Tile',
        fields=[
            'static_image',
            'static_bg_color',
            'static_title',
            'static_text',
            'static_text_color',
            'static_text_shadow',
            'static_hor_text_position',
        ]
    )

    form.widget(static_image=ImageRelatedItemFieldWidget)
    static_image = schema.List(
        title=u'Slide Image',
        description=u'Image on static tile to create parallax effect.',
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    static_bg_color = schema.Choice(
        title=u'Background Color',
        description=u'If no image selected, tile will be this color',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('black', 'black', u'Black'),
            SimpleTerm('white', 'white', u'White'),
        ]),
        default=u'white'
    )

    static_title = schema.TextLine(
        title=u'Slide Title',
        description=u'Will be omitted if blank',
        required=False,
        default=u'')

    static_text = schema.Text(
        title=u'Slide Text',
        description=u'Will be omitted if blank',
        required=False,
        default=u'')

    static_text_color = schema.Choice(
        title=u'Text Color',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('black', 'black', u'Black'),
            SimpleTerm('white', 'white', u'White'),
        ]),
        default=u'black'
    )

    static_text_shadow = schema.Choice(
        title=u'Text Shadow',
        description=u'Adds a shadow to the text over the image.',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('None', 'None', u'None'),
            SimpleTerm('black', 'black', u'Black'),
            SimpleTerm('white', 'white', u'White'),
        ]),
        default=u'None'
    )

    static_hor_text_position = schema.Choice(
        title=u'Slide Text Position (Horizontal)',
        description=u'How the text will be horizontally positioned on the tile.',
        vocabulary=SimpleVocabulary([
            SimpleTerm('start', 'start', u'Left (Half Width)'),
            SimpleTerm('center', 'center', u'Center (Full Width)'),
            SimpleTerm('end', 'end', u'Right (Half Width)'),
        ]),
        default=u'center'
    )
