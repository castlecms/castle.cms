from castle.cms.tiles.base import BaseTile
from castle.cms.widgets import FocalPointSelectFieldWidget
from castle.cms.widgets import ImageRelatedItemFieldWidget
from castle.cms.widgets import RelatedItemFieldWidget
from plone.autoform import directives as form
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from plone.tiles.interfaces import IPersistentTile
from Products.CMFPlone.interfaces.controlpanel import IImagingSchema
from zope import schema
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import implements
from zope.interface import Invalid
from zope.interface import invariant
from zope.interface import provider
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@provider(IContextSourceBinder)
def image_scales(context):
    values = []
    registry = getUtility(IRegistry)
    settings = registry.forInterface(IImagingSchema,
                                     prefix="plone",
                                     check=False)
    values.append(SimpleTerm('', '', 'Original'))
    for allowed_size in settings.allowed_sizes:
        name = allowed_size.split()[0]
        values.append(SimpleTerm(name, name, allowed_size))
    return SimpleVocabulary(values)


class ImageTile(BaseTile):
    implements(IPersistentTile)

    def render(self):
        return self.index()

    def get_image(self):
        image = self.data.get('image')
        if not image:
            return
        return self.utils.get_object(self.data['image'][0])

    def get_link(self):
        link = self.data.get('link')
        if not link:
            return
        try:
            return self.utils.get_object(link[0])
        except:
            pass


class IImageTileSchema(model.Schema):

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
            if obj.portal_type != 'Image':
                raise Invalid('Must provide image file')

    scale = schema.Choice(
        title=u'Scale',
        required=True,
        source=image_scales,
        default=u'large'
    )

    display_type = schema.Choice(
        title=u'Display type',
        required=True,
        default=u'natural',
        vocabulary=SimpleVocabulary([
            SimpleTerm('natural', 'natural', u'Natural'),
            SimpleTerm('fullwidth', 'fullwidth', u'Natural(Full width)'),
            SimpleTerm('portrait', 'portrait', u'Portrait'),
            SimpleTerm('landscape', 'landscape', u'Landscape'),
            SimpleTerm('square', 'square', u'Square'),
            SimpleTerm('short', 'short', u'Short'),
        ])
    )

    caption = schema.TextLine(
        title=u'Caption',
        description=u'The caption shows under the image. This is different than the summary'
                    u' field on the image',
        required=False
    )

    form.widget(override_focal_point=FocalPointSelectFieldWidget)
    override_focal_point = schema.Text(
        title=u'Override Focal point',
        default=u'',
        required=False
    )

    form.widget(link=RelatedItemFieldWidget)
    link = schema.List(
        title=u"Link",
        description=u"Content to link this image to.",
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    @invariant
    def validate_link(data):
        if data.link and len(data.link) != 1:
            raise Invalid("Must select 1 link only")
