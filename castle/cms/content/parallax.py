from zope.interface import implements
from castle.cms.interfaces import IParallax
from plone.dexterity.content import Item


class Parallax(Item):
    implements(IParallax)
