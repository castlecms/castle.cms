from plone.app.contenttypes.content import File
from zope.interface import implementer

from castle.cms.interfaces import IVideo


@implementer(IVideo)
class Video(File):
    pass
