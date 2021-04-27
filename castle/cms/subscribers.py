from castle.cms import audit
from castle.cms import tasks
from castle.cms.constants import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from castle.cms.lead import check_lead_image
from plone import api
from plone.api.exc import CannotGetPortalError
from plone.app.blocks.interfaces import DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.dexterity.behaviors.metadata import IOwnership
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.app.event.base import localized_now
from plone.app.versioningbehavior.utils import get_change_note
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFCore.interfaces._content import IFolderish
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.browser.syndication.settings import FeedSettings
from zope.component import getUtility
from zope.globalrequest import getRequest
from zope.interface import Interface
import logging


logger = logging.getLogger('castle.cms')


try:
    from z3c.relationfield.interfaces import IRelationBrokenEvent
except ImportError:
    class IRelationBrokenEvent(Interface):
        pass


def on_content_state_changed(obj, event):
    obj.reindexObject(idxs=['has_private_parents'])
    if IFolderish.providedBy(obj):
        tasks.reindex_children.delay(obj, ['has_private_parents'])


def on_file_edit(obj, event):
    if IRelationBrokenEvent.providedBy(event):
        # these trigger too much!
        return

    try:
        tasks.file_edited.delay(obj)
    except CannotGetPortalError:
        pass


def on_file_delete(obj, event):
    try:
        tasks.aws_file_deleted.delay(IUUID(obj))
    except CannotGetPortalError:
        pass


def on_file_state_changed(obj, event):
    try:
        tasks.workflow_updated.delay(obj)
    except CannotGetPortalError:
        pass


def on_content_created(obj, event):
    if obj.portal_type == 'Dashboard':
        return
    metadata = IPublication(obj, None)
    if metadata is not None:
        if metadata.effective is None:
            metadata.effective = localized_now(obj)
    _touch_contributors(obj)

    if obj.portal_type == 'Collection':
        # enable syndication on type by default
        settings = FeedSettings(obj)
        settings.enabled = True

    adapted = ILayoutAware(obj, None)
    if adapted:
        if not adapted.content and not adapted.contentLayout:
            registry = getUtility(IRegistry)
            try:
                default_layout = registry['%s.%s' % (
                    DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY,
                    obj.portal_type.replace(' ', '-'))]
                adapted.contentLayout = default_layout
            except (KeyError, AttributeError):
                pass
            try:
                default_layout = registry['%s.%s' % (
                    DEFAULT_SITE_LAYOUT_REGISTRY_KEY,
                    obj.portal_type.replace(' ', '-'))]
                adapted.pageSiteLayout = default_layout
            except (KeyError, AttributeError):
                pass

    try:
        tasks.scan_links.delay('/'.join(obj.getPhysicalPath()))
    except CannotGetPortalError:
        pass

    obj.reindexObject()


def on_content_modified(obj, event):
    obj.changeNote = get_change_note(getRequest())
    if IRelationBrokenEvent.providedBy(event):
        # these trigger too much!
        return
    if obj.portal_type == 'Dashboard':
        return
    try:
        tasks.scan_links.delay('/'.join(obj.getPhysicalPath()))
    except CannotGetPortalError:
        pass
    _touch_contributors(obj)


def on_edit_finished(obj, event):
    """
    on forms submission of done editing page...
    """
    check_lead_image(obj, request=getRequest())


def on_object_event(obj, event):
    if IRelationBrokenEvent.providedBy(event):
        # these trigger too much!
        return
    audit.event(obj, event)


def on_config_modified_event(event):
    # Handling for theme change being triggered.
    try:
        if 'IThemeSettings' in event.record.__name__:
            on_theme_event(event)
        else:
            audit.event(event)
    except Exception:
        logger.warn('Event %s unable to be logged.' % event.record.__name__)


def on_theme_event(event):
    # Prevents theme change from logging several times
    if 'currentTheme' in event.record.__name__:
        audit.event(event)


def on_trash_emptied(obj):
    audit.event(obj)


def on_cache_invalidated(obj):
    audit.event(obj)


def on_pas_event(event):
    audit.event(event)


def _touch_contributors(obj):
    ownership = IOwnership(obj, None)
    if ownership is not None:
        # current user id
        try:
            user_id = api.user.get_current().getId()
            if (user_id not in ownership.creators and
                    user_id not in ownership.contributors):
                ownership.contributors = ownership.contributors + (
                    user_id.decode('utf8'),)
        except Exception:
            pass


def on_trash_transitioned(obj, event):
    api.portal.show_message(
        'You are not allowed to transition an item in the recycling bin.',
        request=getRequest(), type='error')
    raise WorkflowException(
        'You are not allowed to transition an item in the recycling bin.')


def on_youtube_video_edit(obj, event):
    if IRelationBrokenEvent.providedBy(event):
        # these trigger too much!
        return

    value = getattr(obj, '_youtube_video_id', None)
    if value:
        try:
            tasks.youtube_video_edited.delay(obj)
        except CannotGetPortalError:
            pass


def on_youtube_video_delete(obj, event):
    value = getattr(obj, '_youtube_video_id', None)
    if value:
        try:
            tasks.youtube_video_deleted.delay(value)
        except CannotGetPortalError:
            pass


def on_youtube_video_state_changed(obj, event):
    value = getattr(obj, '_youtube_video_id', None)
    if value:
        try:
            tasks.youtube_video_state_changed.delay(obj)
        except CannotGetPortalError:
            pass
