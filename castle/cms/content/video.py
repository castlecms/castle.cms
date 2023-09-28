from zope.interface import implementer
from castle.cms.interfaces import IVideo
from plone.app.contenttypes.content import File


@implementer(IVideo)
class Video(File):
    pass
