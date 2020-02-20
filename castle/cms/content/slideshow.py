from zope.interface import implements
from castle.cms.interfaces import ISlideshow
from plone.dexterity.content import Item


class Slideshow(Item):
    implements(ISlideshow)
