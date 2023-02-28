from plone.dexterity.content import Item
from zope.interface import implementer

from castle.cms.interfaces import IParallax


@implementer(IParallax)
class Parallax(Item):
    pass
