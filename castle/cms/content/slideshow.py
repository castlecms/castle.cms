from plone.dexterity.content import Item
from zope.interface import implementer

from castle.cms.interfaces import ISlideshow


@implementer(ISlideshow)
class Slideshow(Item):
    pass
