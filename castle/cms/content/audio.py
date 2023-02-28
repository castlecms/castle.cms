from plone.app.contenttypes.content import File
from zope.interface import implementer

from castle.cms.interfaces import IAudio


@implementer(IAudio)
class Audio(File):
    pass
