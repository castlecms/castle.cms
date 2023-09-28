from zope.interface import implementer
from castle.cms.interfaces import ISlideshow
from plone.dexterity.content import Item


@implementer(ISlideshow)
class Slideshow(Item):
    pass
