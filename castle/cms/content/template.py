from zope.interface import implementer
from castle.cms.interfaces import ITemplate
from plone.dexterity.content import Item


class Template(Item):
    implements(ITemplate)
