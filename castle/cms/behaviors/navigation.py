from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider

import zope.schema as schema


@provider(IFormFieldProvider)
class INavigationLabel(model.Schema):

    model.fieldset(
        'settings',
        fields=['navigation_label'],
    )

    navigation_label = schema.TextLine(
        title=u'Navigation Label',
        description=u'Label that shows up in Navigation menus instead of title. '
                    u'Can be left blank',
        required=False
    )


@implementer(INavigationLabel)
@adapter(IDexterityContent)
class NavigationLabel(object):

    def __init__(self, context):
        self.context = context
