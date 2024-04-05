from plone.app.contenttypes import _
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile import field as namedfile
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from zope.schema.interfaces import IFromUnicode

import zope.schema as schema

# TODO: Currently attempting to convert the image schema
# to a list of namedBlobImages.
# The list requires the IFromUnicode interface to function,
# though it causes the 'multimedia' tab to disappear in the modal.
# These two interfaces may not be compatible together

def multi_provider(*interfaces):
    def decorator(cls):
        for interface in interfaces:
            provider(interface)(cls)
        return cls
    return decorator

# @provider(IFormFieldProvider)
@multi_provider(IFormFieldProvider, IFromUnicode)
class IRequiredLeadImage(ILeadImage):

    # image = namedfile.NamedBlobImage(
    #     title=_(u'label_leadimage', default=u'Lead Image'),
    #     description=_(u'help_leadimage', default=u''),
    #     required=True
    # )
    image = schema.List(
        title=_(u'label_leadimage', default=u'Lead Image(s)'),
        description=_(u'help_leadimage', default=u''),
        required=True,
        value_type=namedfile.NamedBlobImage()
    )

    image_caption = schema.TextLine(
        title=_(u'label_leadimage_caption', default=u'Lead Image Caption'),
        description=_(u'help_leadimage_caption', default=u''),
        required=False,
    )


@implementer(IRequiredLeadImage)
@adapter(IDexterityContent)
class RequiredLeadImage(object):

    def __init__(self, context):
        self.context = context
