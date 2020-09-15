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
                    u'This does not change the position of the text section selected above. '
                    u'(Note: this is ignored on smaller screens)',
        vocabulary=SimpleVocabulary([
            SimpleTerm('left', 'left', u'Left'),
            SimpleTerm('center', 'center', u'Center'),
        ]),
        required=True,
        default=u'center'
    )

    justify_wrapped_text = schema.Bool(
        title=u'Justify Wrapped Text Lines',
        description=u'Select this option to force any text line that wraps to more than one line to take up the entire width. ' # noqa
                    u'This will assure that there are no gaps to the left and/or right when text fills the whole line, regardless of Text Alignment Choice above.', # noqa 
        default=False,
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
