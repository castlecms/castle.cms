# -*- coding: utf-8 -*-
from zope.component import getAdapters
from plone.folder.interfaces import IOrdering
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import implements
from plone.app.contenttypes import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.dexterity.interfaces import IDexterityContainer
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from zope import schema


class AvailableOrderSource(object):
    implements(IContextSourceBinder)

    ignored = (
        'partial',
    )

    labels = {
        '': 'New items added to bottom',
        'reversed': 'New items add to top'
    }

    def __init__(self):
        pass

    def get_label(self, name):
        if name in self.labels:
            return self.labels[name]
        return name.capitalize()

    def __call__(self, context):
        terms = []
        for name in sorted([name for name, _ in getAdapters((context,), provided=IOrdering)]):
            if name in self.ignored:
                continue
            terms.append(SimpleVocabulary.createTerm(name, name, self.get_label(name)))
        return SimpleVocabulary(terms)


@provider(IFormFieldProvider)
class IFolderOrder(model.Schema):

    model.fieldset('settings', label=_(u"Settings"),
                   fields=['folder_order'])

    folder_order = schema.Choice(
        title=_(u'Folder order'),
        description=u"Order in which new content is added to container",
        required=True,
        default=u'',
        source=AvailableOrderSource()
    )


@implementer(IFolderOrder)
@adapter(IDexterityContainer)
class FolderOrder(object):

    def __init__(self, context):
        self.context = context

    def _set_folder_order(self, value):
        if isinstance(value, unicode):
            value = value.encode('utf8')
        self.context._ordering = value

    def _get_folder_order(self):
        if hasattr(self.context, '_ordering'):
            return self.context._ordering.decode('utf8')

    folder_order = property(_get_folder_order, _set_folder_order)
