from plone.app.versioningbehavior import _
from plone.app.versioningbehavior.behaviors import IVersionable as OldIVersionable
from plone.autoform.interfaces import IFormFieldProvider
from zope import schema
from zope.interface import alsoProvides
from zope.interface import Interface


class IVersionable(OldIVersionable):

    changeNote = schema.TextLine(
        title=_(u'label_change_note', default=u'Change Note'),
        description=_(u'help_change_note',
                      default=u'Enter a comment that describes the changes you made.'),
        required=True)


alsoProvides(IVersionable, IFormFieldProvider)


class IVersioningSupport(Interface):
    """
    Marker Interface for the IVersionable behavior.
    """
