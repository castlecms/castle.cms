from plone.app.contenttypes import _
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile import field as namedfile
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from plone.autoform import directives as form
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope.interface import provider
from plone.app.z3cform.widget import RelatedItemsWidget as BaseRelatedItemsWidget  # noqa


import zope.schema as schema


# Needed to prevent circular dependency
class RelatedItemsWidget(BaseRelatedItemsWidget):
    initialPath = None
    base_criteria = []

    def _base_args(self):
        args = super(RelatedItemsWidget, self)._base_args()
        args['pattern_options']['width'] = ''
        args['pattern_options']['initialPath'] = self.initialPath
        base_criteria = self.base_criteria[:]
        args['pattern_options']['baseCriteria'] = base_criteria
        return args


class ImageRelatedItemWidget(RelatedItemsWidget):

    initialPath = '/image-repository'

    def _base_args(self):
        args = super(ImageRelatedItemWidget, self)._base_args()
        args['pattern_options']['maximumSelectionSize'] = 1
        args['pattern_options']['selectableTypes'] = ['Image']
        args['pattern_options']['baseCriteria'].append({
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Image', 'Folder']
        })
        return args


@provider(IFormFieldProvider)
class IRequiredLeadImage(model.Schema):

    image = namedfile.NamedBlobImage(
        title=_(u'label_leadimage', default=u'Lead Image'),
        description=_(u'help_leadimage', default=u''),
        required=True
    )

    alternate_image = RelationList(
        title=_(u'label_related_items', default=u'Alternate Lead Image'),
        description=u'An optional secondary image than can be displayed in a Feature tile',
        default=[],
        value_type=RelationChoice(
            title=u'Related',
            vocabulary='plone.app.vocabularies.Catalog'
        ),
        required=False
    )

    form.widget(
        'alternate_image',
        ImageRelatedItemWidget,
        vocabulary='plone.app.vocabularies.Catalog',
        pattern_options={
            'recentlyUsed': True,  # Just turn on. Config in plone.app.widgets.
        }
    )

    fieldset(
        'multimedia',
        label=_(u'Multimedia'),
        fields=['image',
                'alternate_image',
                'image_caption']
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
