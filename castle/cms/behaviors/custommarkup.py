from plone.app.textfield import RichText
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider


@provider(IFormFieldProvider)
class ICustomMarkup(model.Schema):
    custom_markup = RichText(
        title=u'Custom Markup',
        description=u'HTML Markup to be included in some templates and listings',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=False,
    )


@implementer(ICustomMarkup)
@adapter(IDexterityContent)
class CustomMarkup(object):
    def __init__(self, context):
        self.context = context
