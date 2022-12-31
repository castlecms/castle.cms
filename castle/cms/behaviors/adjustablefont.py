from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from castle.cms.constants import (
    DEFAULT_FONT_SIZE_SMALL,
    DEFAULT_FONT_SIZE_MEDIUM,
    DEFAULT_FONT_SIZE_LARGE,
    VALID_CSS_FONT_SIZE_PATTERN,
)
from plone.app.contenttypes import _
from plone.supermodel import directives
from zope.schema import Choice
from zope.schema import TextLine
from zope.interface import invariant
from zope.interface import Invalid
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from plone.api.portal import get_registry_record


adjustable_font_size_fieldset_description = _(
    u'''Use these settings to adjust the font size for the specified tiles on this content item.
Default settings are small: {}, medium: {}, large: {}, but those can be changed in Castle Settings.
Absolute sizes such as 'px' and 'pt' can be used.  Ex: 15px'''.format(
        DEFAULT_FONT_SIZE_SMALL,
        DEFAULT_FONT_SIZE_MEDIUM,
        DEFAULT_FONT_SIZE_LARGE,
    )
)


def get_inline_style(context, tile_type):
    sizes = {
        'default': None,
        'small': get_registry_record(
            'castle.font_size_small',
            default=DEFAULT_FONT_SIZE_SMALL,
        ),
        'medium': get_registry_record(
            'castle.font_size_medium',
            default=DEFAULT_FONT_SIZE_MEDIUM,
        ),
        'large': get_registry_record(
            'castle.font_size_large',
            default=DEFAULT_FONT_SIZE_LARGE,
        ),
        'custom': getattr(
            context,
            'font_size_custom_{}'.format(tile_type),
            None,
        )
    }
    font_size_choice_value = getattr(
        context,
        'font_size_choice_{}'.format(tile_type),
        'default',
    )
    custom_font_size = sizes[font_size_choice_value]
    return (
        '' if not custom_font_size
        else 'font-size: {};'.format(custom_font_size)
    )


def font_size_constraint(provided_font_size):
    return bool(VALID_CSS_FONT_SIZE_PATTERN.match(provided_font_size))


@provider(IFormFieldProvider)
class IAdjustableFontSizeQueryListing(model.Schema):
    directives.fieldset(
        'font_size_adjustments',
        description=adjustable_font_size_fieldset_description,
        label=_(u'Font Size Adjustments'),
        fields=(
            'font_size_choice_query_listing',
            'font_size_custom_query_listing',
        ),
    )
    font_size_choice_query_listing = Choice(
        title=_(u'Font size for Query Listing tile'),
        vocabulary=SimpleVocabulary([
            SimpleTerm('default', 'default', u'Default'),
            SimpleTerm('small', 'small', u'Small'),
            SimpleTerm('medium', 'medium', u'Medium'),
            SimpleTerm('large', 'large', u'Large'),
            SimpleTerm('custom', 'custom', u'Custom'),
        ]),
        default='default',
        required=True,
    )
    font_size_custom_query_listing = TextLine(
        title=u'Custom font size for Query Listing tile',
        description=_(u'Only used if "Custom" is selected immediately above'),
        required=False,
        constraint=font_size_constraint,
    )

    @invariant
    def verify_custom_font_size_specified_if_custom(data):
        font_size_choice_value = getattr(data, 'font_size_choice_query_listing')
        font_size_custom_value = getattr(data, 'font_size_custom_query_listing')
        if font_size_choice_value == 'custom' and not font_size_custom_value:
            raise Invalid(_(
                u'Custom font size must be provided for Query Listing tile if "Custom" is selected choice'
            ))


@implementer(IAdjustableFontSizeQueryListing)
@adapter(IDexterityContent)
class AdjustableFontSizeQueryListing(object):

    def __init__(self, context):
        self.context = context
