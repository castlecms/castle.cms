import plone.supermodel.exportimport
from plone.supermodel.utils import valueToElement
from zope.dottedname.resolve import resolve
from zope.schema.interfaces import IBaseVocabulary
from zope.schema.interfaces import IContextSourceBinder

from zope.schema.interfaces import ISource

from .field import QueryChoice


class QueryChoiceHandler(plone.supermodel.exportimport.ChoiceHandler):
    """
    Extend/override ChoiceHandler to work for QueryChoice field
    """

    def _constructField(self, attributes):
        if 'vocabulary' in attributes:
            try:
                component = resolve(attributes['vocabulary'])
                if IBaseVocabulary.providedBy(component):
                    attributes['vocabulary'] = component
                elif (ISource.providedBy(component) or
                        IContextSourceBinder.providedBy(component)):
                    attributes['source'] = component
                    del attributes['vocabulary']
            except ImportError:
                # regular named vocabulary, leave as is
                pass
        return super(QueryChoiceHandler, self)._constructField(attributes)

    def write(self, field, name, type, elementName='field'):
        element = super(plone.supermodel.exportimport.ChoiceHandler, self).write(
            field,
            name,
            type,
            elementName
        )
        if field.vocabulary is not None:
            value = "{}.{}".format(
                field.vocabulary.__module__,
                field.vocabulary.__name__)
            child = valueToElement(
                self.fieldAttributes['vocabulary'],
                value,
                name='vocabulary',
                force=True
            )
            element.append(child)
        else:
            value = "{}.{}".format(
                field.source.__module__,
                field.source.__name__)
            child = valueToElement(
                self.fieldAttributes['source'],
                value,
                name='source',
                force=True
            )
            element.append(child)

        return element


QueryChoiceImportExportHandler = QueryChoiceHandler(QueryChoice)
