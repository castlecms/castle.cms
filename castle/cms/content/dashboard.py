from castle.cms.interfaces import IDashboard
from plone.dexterity.content import Container
from zope.interface import implementer


class Dashboard(Container):
    implements(IDashboard)
