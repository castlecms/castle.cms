from datetime import datetime
import json
import logging
import logging.config
import os
import threading


from plone import api
from plone.app.iterate.interfaces import IAfterCheckinEvent
from plone.app.iterate.interfaces import ICancelCheckoutEvent
from plone.app.iterate.interfaces import ICheckoutEvent
from plone.app.iterate.interfaces import IWorkingCopyDeletedEvent
from plone.registry.interfaces import IRecordAddedEvent
from plone.registry.interfaces import IRecordRemovedEvent
from plone.registry.interfaces import IRecordModifiedEvent
from plone.uuid.interfaces import IUUID
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from Products.PluggableAuthService.interfaces.events import ICredentialsUpdatedEvent
from Products.PluggableAuthService.interfaces.events import IPrincipalCreatedEvent
from Products.PluggableAuthService.interfaces.events import IPrincipalDeletedEvent
from Products.PluggableAuthService.interfaces.events import IPropertiesUpdatedEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedInEvent
from Products.PluggableAuthService.interfaces.events import IUserLoggedOutEvent
import transaction
from zope.globalrequest import getRequest
from zope.interface import providedBy
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent


from castle.cms.events import ICacheInvalidatedEvent
from castle.cms.events import IMetaTileEditedEvent
from castle.cms.events import ITrashEmptiedEvent
from castle.cms.interfaces import ITrashed
from castle.cms.indexing.hps import add_to_index
from castle.cms.indexing.hps import create_index_if_not_exists
from castle.cms.indexing.hps import is_enabled as hps_is_enabled


logger = logging.getLogger("Plone")

DEFAULT_AUDIT_LOGGER_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'auditlog': {
            'format': '%(asctime)s %(message)s %(type)s "%(name)s" "%(summary)s" %(user)s %(request_uri)s %(date)s %(object)s %(path)s',  # noqa
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.Streamhandler',
            'formatter': 'auditlog',
        },
    },
    'loggers': {
        'auditlogger': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'INFO',
        },
    },
}

# if this path exists, and loads fine as json, then apply the json as logging
# config -- otherwise just pump to stdout
logging_config_file = os.getenv("CASTLE_CMS_AUDIT_LOG_CONFIG_FILE", None)
if logging_config_file is not None and os.path.exists(logging_config_file):
    try:
        with open(logging_config_file, "r") as fin:
            configdict = json.load(fin)
    except Exception:
        configdict = DEFAULT_AUDIT_LOGGER_CONFIG
        logger.error(
            "Couldn't load configuration for auditlogger python logger, "
            "defaulting to stdout", exc_info=True)
else:
    configdict = DEFAULT_AUDIT_LOGGER_CONFIG

logging.config.dictConfig(configdict)
auditlogger = logging.getLogger("auditlogger")


class DefaultRecorder(object):
    valid = True

    def __init__(self, data, event, obj=None):
        self.data = data
        self.event = event
        self.obj = obj

    def __call__(self):
        data = {
            'type': self.data._type,
            'name': self.data.name,
            'summary': self.data.summary,
            'user': api.user.get_current().getId(),
            'date': datetime.utcnow().isoformat(),
            'request_uri': getRequest().URL
        }
        if self.obj is not None:
            data['object'] = IUUID(self.obj)
            data['path'] = '/'.join(self.obj.getPhysicalPath())
        return data


class LoggedInRecorder(DefaultRecorder):
    def __call__(self):
        data = super(LoggedInRecorder, self).__call__()
        data['user'] = self.event.object.getId()
        return data


class WorkflowRecorder(DefaultRecorder):

    @property
    def valid(self):
        return self.event.transition is not None

    def __call__(self):
        data = super(WorkflowRecorder, self).__call__()
        data['summary'] = 'previous: %s, new: %s, transition: %s' % (
            self.event.old_state.title,
            self.event.new_state.title,
            self.event.transition.title,
        )
        return data


class MetaTileRecorder(DefaultRecorder):
    def __call__(self):
        data = super(MetaTileRecorder, self).__call__()
        data['summary'] = 'Slot edited: {}'.format(self.event.tile_id)
        return data


class ConfigModifyRecorder(DefaultRecorder):

    def __call__(self):
        data = super(ConfigModifyRecorder, self).__call__()
        try:
            data['summary'] = 'Configuration Record '
            '%s modified. Old value: %s, New value: %s' % (
                self.event.record,
                self.event.oldValue,
                self.event.newValue
            )
        except AttributeError:
            data['summary'] = 'Configuration Record '
            '%s modified.' % self.event.record
        return data


class CacheInvalidatedRecorder(DefaultRecorder):

    def __call__(self):
        data = super(CacheInvalidatedRecorder, self).__call__()
        if self.event.object.success:
            data['summary'] = 'The following urls have been purged: '
            '%s' % self.event.object.purged
        else:
            data['summary'] = 'Cache invalidation failure. '
            'Make sure caching proxies are properly configured.'
        return data


class ContentTypeChangeNoteRecorder(DefaultRecorder):

    def __call__(self):
        data = super(ContentTypeChangeNoteRecorder, self).__call__()
        data['summary'] = 'Change Note Summary: %s' % \
                          self.event.object.changeNote
        return data


class AuditData(object):

    def __init__(self, _type, name, summary=None,
                 recorder_class=DefaultRecorder):
        self._type = _type
        self.name = name
        self.summary = summary
        self.recorder_class = recorder_class

    def get_recorder(self, event, obj=None):
        return self.recorder_class(self, event, obj)


_registered = {
    IAfterCheckinEvent: AuditData('working copy support', 'Check in'),
    ICheckoutEvent: AuditData('working copy support', 'Check out'),
    ICancelCheckoutEvent: AuditData('working copy support', 'Cancel checkout'),
    IWorkingCopyDeletedEvent: AuditData(
        'working copy support', 'Working copy deleted'),
    IObjectAddedEvent: AuditData('content', 'Created'),
    IObjectCopiedEvent: AuditData('content', 'Copied'),
    IObjectModifiedEvent: AuditData(
        'content', 'Modified',
        recorder_class=ContentTypeChangeNoteRecorder),
    IObjectMovedEvent: AuditData('content', 'Moved'),
    IObjectRemovedEvent: AuditData('content', 'Deleted'),
    IPrincipalCreatedEvent: AuditData('user', 'Created'),
    ITrashed: AuditData('content', 'Trashed'),
    IUserLoggedInEvent: AuditData(
        'user', 'Logged in',
        recorder_class=LoggedInRecorder),
    IUserLoggedOutEvent: AuditData('user', 'Logged out'),
    IPrincipalDeletedEvent: AuditData('user', 'Deleted'),
    ICredentialsUpdatedEvent: AuditData('user', 'Password updated'),
    IPropertiesUpdatedEvent: AuditData('user', 'Properties updated'),
    IAfterTransitionEvent: AuditData(
        'workflow', 'Transition',
        recorder_class=WorkflowRecorder),
    IMetaTileEditedEvent: AuditData(
        'slots', 'Slot edited',
        recorder_class=MetaTileRecorder),
    IRecordAddedEvent: AuditData(
        'configuration', 'Added',
        recorder_class=ConfigModifyRecorder),
    IRecordModifiedEvent: AuditData(
        'configuration', 'Modified',
        recorder_class=ConfigModifyRecorder),
    IRecordRemovedEvent: AuditData(
        'configuration', 'Removed',
        recorder_class=ConfigModifyRecorder),
    ITrashEmptiedEvent: AuditData('content', 'Trash Emptied'),
    ICacheInvalidatedEvent: AuditData(
        'content', 'Cache Invalidated',
        recorder_class=CacheInvalidatedRecorder)
}


def _check_for_index(index_name):
    mapping = {'properties': {
        'type': {'store': False, 'type': 'text', 'index': False},
        'name': {'store': False, 'type': 'text', 'index': False},
        'summary': {'store': False, 'type': 'text', 'index': False},
        'user': {'store': False, 'type': 'text', 'index': False, 'analyzer': 'keyword'},
        'request_uri': {'store': False, 'type': 'text', 'index': False},
        'date': {'store': False, 'type': 'date'},
        'object': {'store': False, 'type': 'text', 'index': False},
        'path': {'store': False, 'type': 'text', 'index': False},
    }}
    create_index_if_not_exists(index_name, mapping)


def get_audit_index_name(site_path=None):
    if site_path is not None:
        index_name = site_path
    else:
        index_name = '/'.join(api.portal.get().getPhysicalPath())
    return "{}-audit".format(index_name.replace('/', '').replace(' ', '').lower())


def _record(site_path, data):
    auditlogger.info(site_path, data)
    index_name = get_audit_index_name(site_path)
    add_to_index(index_name, data, create_on_exception=_check_for_index)


def record(success, recorder, site_path):
    if not success:
        return
    if recorder.valid:
        data = recorder()
        auditlogger.info(site_path, data)
        thread = threading.Thread(
            target=_record,
            args=(
                site_path,
                data,
            ))
        thread.start()


def event(obj, event=None):
    if event is None:
        # some events don't include object
        event = obj
        obj = None

    iface = providedBy(event).declared[0]
    if iface not in _registered:
        return

    if not hps_is_enabled():
        return

    if obj is not None and ITrashed.providedBy(obj):
        # special handling for ITrashed...
        # we don't want to record transition events for trashing
        # and we want a special psuedo trash event
        # then, we still want an event when it gets deleted for good
        if iface not in (IAfterTransitionEvent, IObjectRemovedEvent):
            # dive out if not IAfterTransitionEvent or object removed event
            return
        if iface == IObjectRemovedEvent:
            audit_data = _registered[iface]
        else:
            audit_data = _registered[ITrashed]
    else:
        audit_data = _registered[iface]

    recorder = audit_data.get_recorder(event, obj)
    site_path = '/'.join(api.portal.get().getPhysicalPath())
    transaction.get().addAfterCommitHook(record, args=(recorder, site_path))
