from plone.namedfile.interfaces import INamedImage
from zope.interface import Attribute
from OFS.interfaces import IApplication
from plone.app.contenttypes.interfaces import IFile
from plone.supermodel import model
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs
from zope.interface import Interface
from zope import schema
from plone.api.portal import get_registry_record
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory


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


@provider(IContextAwareDefaultFactory)
def get_default_text(context):
    return get_registry_record('castle.resource_slide_view_more_link_text', None)


@provider(IContextAwareDefaultFactory)
def get_default_url(context):
    return get_registry_record('castle.resource_slide_view_more_link_url', None)


class ISlideshow(Interface):

    model.fieldset(
        'Resource Slide',
        fields=['show_view_more_link',
                'view_more_link_text',
                'update_default_link_text',
                'view_more_link_url',
                'update_default_link_url']
    )
    custom_dom_id = schema.Text(
        title=u"ID for the slideshow element",
        description=u"If custom styling desired for this slideshow",
        required=False
    )

    show_view_more_link = schema.Bool(
        title=u'Show "View More" link?',
        description=u'The fields below only matter if this box is checked',
        required=True,
        default=False)

    view_more_link_text = schema.TextLine(
        title=u"View More link text",
        description=u'The text a user sees for the optional link at the bottom of the slideshow resource slide. ' # noqa
                    u'This link will be omitted if "View More Link" is unchecked or if the link text or link URL is empty.', # noqa
        required=False,
        defaultFactory=get_default_text)

    update_default_link_text = schema.Bool(
        title=u"Make this the default link text for all slideshows?",
        description=u'This only changes the default value. It will not modify any existing content',
        required=True,
        default=False)

    # directives.widget('make_default_text', SingleCheckBoxFieldWidget)
    view_more_link_url = schema.URI(
        title=u"View More link URL",
        description=u'The URL to which the user is directed for the optional link at the bottom of the slideshow resource slide. ' # noqa
                    u'This link will be omitted if "View More Link" is unchecked or if the link text or link URL is empty.', # noqa
        required=False,
        defaultFactory=get_default_url)

    # directives.widget('make_default_text', SingleCheckBoxFieldWidget)
    update_default_link_url = schema.Bool(
        title=u"Make this the default link url for all slideshows?",
        description=u'This only changes the default value. It will not modify any existing content',
        required=True,
        default=False)


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
