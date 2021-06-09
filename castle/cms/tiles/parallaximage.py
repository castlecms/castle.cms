from castle.cms.tiles.base import BaseTile
from castle.cms.widgets import ImageRelatedItemFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from plone.tiles.interfaces import IPersistentTile
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope import schema
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import implements
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class ParallaxImageTile(BaseTile):
    implements(IPersistentTile)
    index = ViewPageTemplateFile('templates/parallaximage.pt')

    def get_image(self):
        image = self.data.get('image')
        if not image:
            return
        return self.utils.get_object(self.data['image'][0])

    def get_width_values(self):
        scale_value = self.data.get('width')
        image_widths = ['100%', '200%', '300%', '400%', '500%']
        image_margins = ['0%', '-50%', '-100%', '-150%', '-200%']
        text_widths = ['100%', '50%', '33%', '25%', '20%']
        text_margins = ['0%', '25%', '33%', '37.5%', '40%']
        width_values = {'img_width': image_widths[scale_value],
                        'img_margin': image_margins[scale_value],
                        'txt_width': text_widths[scale_value],
                        'txt_margin': text_margins[scale_value]}
        return width_values


class IParallaxImageTileSchema(model.Schema):

    form.widget(image=ImageRelatedItemFieldWidget)
    image = schema.List(
        title=u"Image",
        description=u"Reference image on the site.",
        required=True,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    @invariant
    def validate_image(data):
        if data.image and len(data.image) != 1:
            raise Invalid("Must select 1 image")
        if data.image:
            utils = getMultiAdapter((getSite(), getRequest()),
                                    name="castle-utils")
            obj = utils.get_object(data.image[0])
            if not obj or obj.portal_type != 'Image':
                raise Invalid('Must provide image file')

    height = schema.Choice(
        title=u'Height of parallax image',
        description=u'Represent the height (in pixels) that the parallax image will be.',
        required=True,
        default=u'400px',
        vocabulary=SimpleVocabulary([
            SimpleTerm('100px', '100px', '100px'),
            SimpleTerm('200px', '200px', '200px'),
            SimpleTerm('300px', '300px', '300px'),
            SimpleTerm('400px', '400px', '400px'),
            SimpleTerm('500px', '500px', '500px'),
            SimpleTerm('600px', '600px', '600px'),
            SimpleTerm('700px', '700px', '700px'),
            SimpleTerm('800px', '800px', '800px'),
            SimpleTerm('900px', '900px', '900px'),
            SimpleTerm('1000px', '1000px', '1000px'),
        ])
    )

    width = schema.Choice(
        title=u'Width of parallax image',
        description=u'Represent the width (in percentage) that the parallax image will be.',
        required=True,
        default=0,
        vocabulary=SimpleVocabulary([
            SimpleTerm(0, '100%', '100%'),
            SimpleTerm(1, '200%', '200%'),
            SimpleTerm(2, '300%', '300%'),
            SimpleTerm(3, '400%', '400%'),
            SimpleTerm(4, '500%', '500%'),
        ])
    )

    heading_text = schema.TextLine(
        title=u'Heading Text',
        description=u'',
        required=False,
    )

    heading_size = schema.Choice(
        title=u'Heading Size',
        description=u'',
        default=u'36px',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('36px', 'h1', 'h1'),
            SimpleTerm('30px', 'h2', 'h2'),
            SimpleTerm('24px', 'h3', 'h3'),
            SimpleTerm('18px', 'h4', 'h4'),
            SimpleTerm('14px', 'h5', 'h5'),
            SimpleTerm('12px', 'h6', 'h6'),
        ])
    )

    heading_color = schema.Choice(
        title=u'Heading Color',
        description=u'Select between black or white for text color',
        default=u'black',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('black', 'black', 'Black'),
            SimpleTerm('white', 'white', 'White'),
        ])
    )

    body_text = schema.Text(
        title=u'Body Text',
        description=u'',
        required=False,
    )

    body_size = schema.Choice(
        title=u'Body Size',
        description=u'',
        default=u'12px',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('20px', '20px', '20px'),
            SimpleTerm('18px', '18px', '18px'),
            SimpleTerm('16px', '16px', '16px'),
            SimpleTerm('14px', '14px', '14px'),
            SimpleTerm('12px', '12px', '12px'),
            SimpleTerm('10px', '10px', '10px'),
        ])
    )

    body_color = schema.Choice(
        title=u'Body Color',
        description=u'Select between black or white for text color',
        default=u'black',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('black', 'black', 'Black'),
            SimpleTerm('white', 'white', 'White'),
        ])
    )

    text_position = schema.Choice(
        title=u'Text Position',
        description=u'Dictates where text will be positioned over parallax image',
        default=u'left',
        required=True,
        vocabulary=SimpleVocabulary([
            SimpleTerm('left', 'left', 'Left'),
            SimpleTerm('center', 'center', 'Center'),
            SimpleTerm('right', 'right', 'Right'),
        ])
    )
