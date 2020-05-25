from castle.cms.tiles.base import BaseTile
from castle.cms.widgets import ImageRelatedItemFieldWidget
from castle.cms.widgets import SlideRelatedItemsFieldWidget

from castle.cms.widgets import VideoRelatedItemsFieldWidget
from plone.supermodel import model
from plone.autoform import directives as form
from Products.CMFPlone.resources import add_resource_on_request
from zope import schema
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


# with open('castle/cms/static/scripts/slide.js', 'r') as file:
#     javascript = file.read()
#     javascript = javascript.replace('\n', '')
#     javascript = u'javascript:{}'.format(javascript)

class SlideTile(BaseTile):

    @property
    def relatedItems(self):
        return self.context.relatedItems

    @property
    def slide_type(self):
        return self.data.get('display_type', 'background-image')

class ISlideTileSchema(model.Schema):
    form.widget('display_type', onchange=u'javascript:onSlideTypeChange(event)')
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

    vert_text_position = schema.Choice(
        title=u"Slide Text Position (Vertical)",
        vocabulary=SimpleVocabulary([
            SimpleTerm('top', 'top', u'Top'),
            SimpleTerm('middle', 'middle', u'Middle'),
            SimpleTerm('bottom', 'bottom', u'Bottom'),
        ]),
        required=False,
        default=u'middle'
    )

    hor_text_position = schema.Choice(
        title=u"Slide Text Position (Horizontal)",
        vocabulary=SimpleVocabulary([
            SimpleTerm('start', 'start', u'Left'),
            SimpleTerm('center', 'center', u'Center'),
            SimpleTerm('end', 'end', u'Right'),
        ]),
        required=False,
        default=u'center'
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

    form.widget(related_items=SlideRelatedItemsFieldWidget)
    related_items = schema.List(
        title=u"Related Items",
        description=u"Items to include on Reference slide",
        required=False,
        default=[],
        value_type=schema.Choice(
            # vocabulary='plone.app.vocabularies.Catalog'
            vocabulary='castle.cms.vocabularies.ProvidesTitleSummaryLeadImage'
        )
    )
