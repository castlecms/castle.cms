from zope.interface import implementer
from castle.cms.interfaces import IAudio
from plone.app.contenttypes.content import File


@implementer(IAudio)
class Audio(File):
    pass
