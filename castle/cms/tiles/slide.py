from castle.cms.tiles.base import BaseTile
from castle.cms.widgets import ImageRelatedItemFieldWidget
from castle.cms.widgets import SlideRelatedItemsFieldWidget
from castle.cms.widgets import VideoRelatedItemsFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class SlideTile(BaseTile):

    @property
    def relatedItems(self):
        return self.context.relatedItems

    @property
    def slide_type(self):
        return self.data.get('display_type', 'background-image')


class ISlideTileSchema(model.Schema):

    model.fieldset(
        'type_and_text',
        label=u'Type & Text',
        fields=[
            'display_type',
            'title',
            'text',
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
        required=False,
        default=u'')

    text = schema.Text(
        title=u'Slide Text',
        description=u'Will be omitted if blank',
        required=False,
        default=u'')

    #######################################################################################################
    model.fieldset(
        'text_positioning',
        label=u'Text Positioning',
        fields=[
            'hor_text_position',
            'vert_text_position',
            'text_alignment',
            'customize_left_slide_mobile',
            'justify_wrapped_text',
        ]
    )

    hor_text_position = schema.Choice(
        title=u"Slide Text Position (Horizontal)",
        vocabulary=SimpleVocabulary([
            SimpleTerm('start', 'start', u'Left'),
            SimpleTerm('center', 'center', u'Center'),
            SimpleTerm('end', 'end', u'Right'),
        ]),
        required=True,
        default=u'center'
    )

    vert_text_position = schema.Choice(
        title=u"Slide Text Position (Vertical)",
        vocabulary=SimpleVocabulary([
            SimpleTerm('top', 'top', u'Top'),
            SimpleTerm('middle', 'middle', u'Middle'),
            SimpleTerm('bottom', 'bottom', u'Bottom'),
        ]),
        required=True,
        default=u'middle'
    )

    text_alignment = schema.Choice(
        title=u"Slide Text Alignment",
        description=u'The alignment of slide text relative to other text on the page. '
                    u'This does not change the position of the text section selected above.',
        vocabulary=SimpleVocabulary([
            SimpleTerm('left', 'left', u'Left'),
            SimpleTerm('center', 'center', u'Center'),
            SimpleTerm('right', 'right', u'Right'),
        ]),
        required=True,
        default=u'center'
    )

    customize_left_slide_mobile = schema.Bool(
        title=u'Use Different Alignment & Position Values for Mobile',
        description=u'On small screens such as mobile devices, Left Image Right Text and Left Video Right Text slides are displayed exactly like background slides. '  # noqa
                    u'Select this option to display the "Mobile Text Positioning" tab, which allows different position and alignment values for this slide on small screens.',  # noqa
        default=False,
    )

    justify_wrapped_text = schema.Bool(
        title=u'Justify Wrapped Text Lines',
        description=u'Select this option to force any text line that wraps to more than one line to take up the entire width. ' # noqa
                    u'This will assure that there are no gaps to the left and/or right when text fills the whole line, regardless of Text Alignment Choice above.', # noqa 
        default=False,
    )

    #######################################################################################################
    model.fieldset(
        'left_slide_mobile_text_positioning',
        label=u'Mobile Text Positioning',
        description=u'On small screens such as mobile devices, Left Image Right Text and Left Video Right Text slides are displayed exactly like background slides. '  # noqa
                    u'This page allows you to specify different text position and alignment values that apply to smaller displays only.', # noqa
        fields=[
            'left_slide_mobile_hor_text_position',
            'left_slide_mobile_vert_text_position',
            'left_slide_mobile_text_alignment',
        ]
    )

    left_slide_mobile_hor_text_position = schema.Choice(
        title=u"Slide Text Position (Horizontal)",
        vocabulary=SimpleVocabulary([
            SimpleTerm('default', 'default', u'Leave Unchanged'),
            SimpleTerm('start', 'start', u'Left'),
            SimpleTerm('center', 'center', u'Center'),
            SimpleTerm('end', 'end', u'Right'),
        ]),
        required=True,
        default=u'default'
    )

    left_slide_mobile_vert_text_position = schema.Choice(
        title=u"Slide Text Position (Vertical)",
        vocabulary=SimpleVocabulary([
            SimpleTerm('default', 'default', u'Leave Unchanged'),
            SimpleTerm('top', 'top', u'Top'),
            SimpleTerm('middle', 'middle', u'Middle'),
            SimpleTerm('bottom', 'bottom', u'Bottom'),
        ]),
        required=True,
        default=u'default'
    )

    left_slide_mobile_text_alignment = schema.Choice(
        title=u"Slide Text Alignment",
        description=u'The alignment of slide text relative to other text on the page. '
                    u'This does not change the position of the text section selected above.',
        vocabulary=SimpleVocabulary([
            SimpleTerm('default', 'default', u'Leave Unchanged'),
            SimpleTerm('left', 'left', u'Left'),
            SimpleTerm('center', 'center', u'Center'),
            SimpleTerm('right', 'right', u'Right'),
        ]),
        required=True,
        default=u'default'
    )

    #######################################################################################################
    model.fieldset(
        'media_settings',
        label=u'Media Settings',
        fields=[
            'image',
            'video',
        ]
    )

    form.widget(image=ImageRelatedItemFieldWidget)
    image = schema.List(
        title=u"Slide Image",
        description=u"Reference image on the site.",
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    form.widget(video=VideoRelatedItemsFieldWidget)
    video = schema.List(
        title=u"Slide Video",
        description=u"Reference video on the site.",
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    #######################################################################################################
    model.fieldset(
        'related_items',
        label=u'Related Items',
        fields=['related_items']
    )

    form.widget('related_items', SlideRelatedItemsFieldWidget)
    related_items = schema.List(
        title=u"Related Items",
        description=u"Items to include on Resource Slide. "
                    u"To be selectable, a content item must contain a Title, Description (Summary), and a Lead Image.", # noqa
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )
