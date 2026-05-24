from plone.app.contenttypes import _
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile import field as namedfile
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from plone.supermodel import model
from plone.supermodel.directives import fieldset

import zope.schema as schema


@provider(IFormFieldProvider)
class IRequiredLeadImage(model.Schema):

    image = namedfile.NamedBlobImage(
        title=_(u'label_leadimage', default=u'Lead Image'),
        description=_(u'help_leadimage', default=u''),
        required=True
    )

    alternate_image = namedfile.NamedBlobImage(
        title=_(u'label_alternateleadimage', default=u'Alternate Lead Image'),
        description=_(u'label_alternateleadimage', default=u'An image to be displayed in tiles that support alternate lead images.'),
        required=False
    )

    image_caption = schema.TextLine(
        title=_(u'label_leadimage_caption', default=u'Lead Image Caption'),
        description=_(u'help_leadimage_caption', default=u''),
        required=False,
    )

    fieldset(
        'multimedia',
        label=_(u'Multimedia'),
        fields=['image',
                'alternate_image',
                'image_caption']
    )


@implementer(IRequiredLeadImage)
@adapter(IDexterityContent)
class RequiredLeadImage(object):

    def __init__(self, context):
        self.context = context
