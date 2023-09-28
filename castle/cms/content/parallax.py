from zope.interface import implementer
from castle.cms.interfaces import IParallax
from plone.dexterity.content import Item


@implementer(IParallax)
class Parallax(Item):
    pass
