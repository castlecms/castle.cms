from zope.interface import implementer
from castle.cms.interfaces import ITemplate
from plone.dexterity.content import Item


@implementer(ITemplate)
class Template(Item):
    pass
