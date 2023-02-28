from plone.dexterity.content import Container
from zope.interface import implementer

from castle.cms.interfaces import IDashboard


@implementer(IDashboard)
class Dashboard(Container):
    pass
