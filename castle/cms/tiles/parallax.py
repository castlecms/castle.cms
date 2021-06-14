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

    # Type and Text
    model.fieldset(
        'type_and_text',
        label=u'Type & Text',
        fields=[
            'display_type',
            'title',
            'title_size',
            'text',
            'text_size',
        ]
    )

    display_type = schema.Choice(
        title=u"Display Type",
        vocabulary=SimpleVocabulary([
            SimpleTerm('background-image', 'background-image', u'Background Image'),  # noqa
            SimpleTerm('left-image-right-text','left-image-right-text', u'Left Image Right Text'),  # noqa
            SimpleTerm('background-video', 'background-video', u'Background Video'),  # noqa
            SimpleTerm('left-video-right-text','left-video-right-text', u'Left Video Right Text'),  # noqa
            SimpleTerm('resource-slide','resource-slide', u'Resource Slide')  # noqa
        ]),
        required=True,
        default='background-image'
    )

    title = schema.TextLine(
        title=u'Slide Title',
        description=u'Will be omitted if blank',
        default=u'')

    title_size = schema.Choice(
        title=u'Title Size',
        description=u'',
        default=u'36px',
        vocabulary=SimpleVocabulary([
            SimpleTerm('36px', 'h1', 'h1'),
            SimpleTerm('30px', 'h2', 'h2'),
            SimpleTerm('24px', 'h3', 'h3'),
            SimpleTerm('18px', 'h4', 'h4'),
            SimpleTerm('14px', 'h5', 'h5'),
            SimpleTerm('12px', 'h6', 'h6'),
        ])
    )

    text = schema.Text(
        title=u'Slide Text',
        description=u'Will be omitted if blank',
        default=u'')

    text_size = schema.Choice(
        title=u'Text Size',
        description=u'',
        default=u'12px',
        vocabulary=SimpleVocabulary([
            SimpleTerm('20px', '20px', '20px'),
            SimpleTerm('18px', '18px', '18px'),
            SimpleTerm('16px', '16px', '16px'),
            SimpleTerm('14px', '14px', '14px'),
            SimpleTerm('12px', '12px', '12px'),
            SimpleTerm('10px', '10px', '10px'),
        ])
    )

    # Text Positioning
    model.fieldset(
        'text_positioning',
        label=u'Text Positioning',
        fields=[
            'hor_text_position',
            'vert_text_position',
            'justify_wrapped_text',
        ]
    )

    hor_text_position = schema.Choice(
        title=u"Slide Text Position (Horizontal)",
        description=u'This setting only applies to large screens. '
                    u'On small screens, Center (Full Width) will always be deisplayed.',
        vocabulary=SimpleVocabulary([
            SimpleTerm('start', 'start', u'Left (Half Width)'),
            SimpleTerm('center', 'center', u'Center (Full Width)'),
            SimpleTerm('end', 'end', u'Right (Half Width)'),
        ]),
        default=u'center'
    )

    vert_text_position = schema.Choice(
        title=u"Slide Text Position (Vertical)",
        vocabulary=SimpleVocabulary([
            SimpleTerm('top', 'top', u'Top'),
            SimpleTerm('middle', 'middle', u'Middle'),
            SimpleTerm('bottom', 'bottom', u'Bottom'),
        ]),
        default=u'middle'
    )

    justify_wrapped_text = schema.Bool(
        title=u'Justify Wrapped Text Lines',
        description=u'Select this option to force any text line that wraps to more than one line to take up the entire width. ' # noqa
                    u'This will assure that there are no gaps to the left and/or right when text fills the whole line, regardless of Text Alignment Choice above.', # noqa 
        default=False,
    )

    # Media Settings
    model.fieldset(
        'media_settings',
        label=u'Media Settings',
        fields=[
            'image',
        ]
    )

    form.widget(image=ImageRelatedItemFieldWidget)
    image = schema.List(
        title=u"Slide Image",
        description=u"Reference image on the site.",
        required=True,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    # @invariant
    # def validate_image(data):
    #     if data.image and len(data.image) != 1:
    #         raise Invalid("Must select 1 image")
    #     if data.image:
    #         utils = getMultiAdapter((getSite(), getRequest()),
    #                                 name="castle-utils")
    #         obj = utils.get_object(data.image[0])
    #         if not obj or obj.portal_type != 'Image':
    #             raise Invalid('Must provide image file')

    # height = schema.Choice(
    #     title=u'Height of parallax image',
    #     description=u'Represent the height (in pixels) that the parallax image will be.',
    #     required=True,
    #     default=u'400px',
    #     vocabulary=SimpleVocabulary([
    #         SimpleTerm('100px', '100px', '100px'),
    #         SimpleTerm('200px', '200px', '200px'),
    #         SimpleTerm('300px', '300px', '300px'),
    #         SimpleTerm('400px', '400px', '400px'),
    #         SimpleTerm('500px', '500px', '500px'),
    #         SimpleTerm('600px', '600px', '600px'),
    #         SimpleTerm('700px', '700px', '700px'),
    #         SimpleTerm('800px', '800px', '800px'),
    #         SimpleTerm('900px', '900px', '900px'),
    #         SimpleTerm('1000px', '1000px', '1000px'),
    #     ])
    # )

    # heading_color = schema.Choice(
    #     title=u'Heading Color',
    #     description=u'Select between black or white for text color',
    #     default=u'black',
    #     required=True,
    #     vocabulary=SimpleVocabulary([
    #         SimpleTerm('black', 'black', 'Black'),
    #         SimpleTerm('white', 'white', 'White'),
    #     ])
    # )

    # body_color = schema.Choice(
    #     title=u'Body Color',
    #     description=u'Select between black or white for text color',
    #     default=u'black',
    #     required=True,
    #     vocabulary=SimpleVocabulary([
    #         SimpleTerm('black', 'black', 'Black'),
    #         SimpleTerm('white', 'white', 'White'),
    #     ])
    # )
