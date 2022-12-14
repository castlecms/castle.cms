from zope.interface import implements
from castle.cms.interfaces import ITemplate
from plone.dexterity.content import Item


class Template(Item):
    implements(ITemplate)
