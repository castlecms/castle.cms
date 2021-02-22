from plone.app.versioningbehavior import _
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from z3c.form.interfaces import IAddForm
from z3c.form.interfaces import IEditForm
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import Interface


class IVersionable(model.Schema):
    """ Behavior for enabling CMFEditions's versioning for dexterity
    content types. Be sure to enable versioning in the plone types
    control-panel for your content type.
    """

    model.fieldset(
        'settings',
        label=_(u'Settings'),
        fields=['versioning_enabled']
    )
    changeNote = schema.TextLine(
        title=_(u'label_change_note', default=u'Change Note'),
        description=_(u'help_change_note',
                      default=u'Enter a comment that describes the changes you made.'),
        required=True)

    versioning_enabled = schema.Bool(
        title=_(u'label_versioning_enabled', default=u'Versioning enabled'),
        description=_(u'help_versioning_enabled',
                      default=u'Enable/disable versioning for this document.'),
        default=True,
        required=False)

    form.order_after(changeNote='*')
    form.omitted('changeNote')
    form.no_omit(IEditForm, 'changeNote')
    form.no_omit(IAddForm, 'changeNote')


alsoProvides(IVersionable, IFormFieldProvider)


class IVersioningSupport(Interface):
    """
    Marker Interface for the IVersionable behavior.
    """


@implementer(IVersionable)
@adapter(IDexterityContent)
class Versionable(object):
    """ The Versionable adapter prohibits dexterity from saving the changeNote
    on the context. It stores it in a request-annotation for later use in
    event-handlers
    The versioning_enabled flag is stored at the context itself.
    """

    def __init__(self, context):
        self.context = context

    @property
    def changeNote(self):
        return ''

    @changeNote.setter
    def changeNote(self, value):
        # store the value for later use
        annotation = IAnnotations(self.context.REQUEST)
        annotation['plone.app.versioningbehavior-changeNote'] = value

    @property
    def versioning_enabled(self):
        return self.context.versioning_enabled

    @versioning_enabled.setter
    def versioning_enabled(self, value):
        setattr(self.context, 'versioning_enabled', value)
