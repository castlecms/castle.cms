from plone.namedfile.interfaces import INamedImage
from zope.interface import Attribute
from OFS.interfaces import IApplication
from plone.app.contenttypes.interfaces import IFile
from plone.supermodel import model
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs
from zope.interface import Interface


class ICastleApplication(IApplication):
    pass


class IDashboard(IHideFromBreadcrumbs):
    pass


class IMedia(model.Schema, IFile):
    pass


class IVideo(IMedia):
    pass


class IAudio(IMedia):
    pass


class ITrashed(Interface):
    """
    marker for object that is in the trash
    """


class IHasDefaultImage(Interface):
    """
    marker interface for content to specify that it has default image
    when a manual image is not specified
    """


class IReferenceNamedImage(INamedImage):
    reference = Attribute('')


class IUploadedToYoutube(Interface):
    """Marker interface for videos that have been uploaded to YouTube"""
