from plone.dexterity.content import Item
from zope.interface import implementer

from castle.cms.interfaces import ITemplate


@implementer(ITemplate)
class Template(Item):
    pass
