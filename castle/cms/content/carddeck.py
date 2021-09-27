from zope.interface import implementer
from castle.cms.interfaces import ICard
from castle.cms.interfaces import ICardDeck
from plone.dexterity.content import Container

@implementer(ICard)
class Card(Container):
    pass


@implementer(ICardDeck)
class CardDeck(Container):
    pass
