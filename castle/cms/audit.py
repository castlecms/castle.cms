"""
Env Vars used:

CASTLE_CMS_AUDIT_LOG_CONFIG_FILE  # specifies a path to a json/dict formatted config for logging
CASTLE_CMS_AUDIT_LOG_INSTANCE     # specifies 'instance' value in audit log schema


Full schema for an audit log message:

schema_version: str  # schema version of log message
schema_type: str     # schema type ("castle.cms.audit")
instance: str        # determined by env var CASTLE_CMS_AUDIT_LOG_INSTANCE
site: str            # either '(zope root)' or the root site path (e.g. '/Castle')
type: str            # audit log type (e.g. 'content', 'workflow', etc)
actionname: str      # previously specified as just 'name', specifies which action for the type
summary: str         # optional short string describing the action
user: str            # username of the account that performed the action
request_uri: str     # the URI of the request that initiated the action
date: str            # ISO date/time the action was performed
object: str          # UUID of object that was affected by action
path: str            # path of object that was affected by action
es2id: Optional[str] # original ES2.x assigned _id -- only present in records migrated from ES2.x storage

"""
from datetime import datetime
import json
import logging
import logging.config
import os


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


logger = logging.getLogger("Plone")

DEFAULT_AUDIT_LOGGER_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'auditlog': {
            'format': '%(asctime)s %(levelname)s %(name)s %(es2id)s %(schema_version)s %(schema_type)s "%(instance)s" "%(site)s" %(type)s "%(actionname)s" "%(summary)s" %(user)s %(request_uri)s %(date)s %(object)s %(path)s',  # noqa
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
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
# config (or try to) -- otherwise just pump to stdout
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

try:
    # note: with 'disable_existing_loggers' set to False, this shouldn't wipeout
    # the config from Plone, etc
    logging.config.dictConfig(configdict)
except Exception:
    logger.error("failed to configure audit logger", exc_info=True)
auditlogger = logging.getLogger("auditlogger")


def get_index_name():
    return os.getenv("CASTLE_CMS_AUDIT_LOG_INDEXNAME", "gelfs-*")


class DefaultRecorder(object):
    valid = True

    def __init__(self, data, event, obj=None):
        self.data = data
        self.event = event
        self.obj = obj

    def __call__(self):
        try:
            user = api.user.get_current().getId()
        except api.exc.CannotGetPortalError:
            # likely means that we are logged in on the zope root, not through a site
            from AccessControl import getSecurityManager
            userobj = getSecurityManager().getUser()
            user = userobj.getUserName()

        try:
            requri = getRequest().URL
        except AttributeError:
            # this might occur on, e.g., tests that don't set up a fake request well
            requri = "(none)"

        data = {
            'es2id': None,  # this is from es2.x conversion. new logs should not have this.
            'type': self.data._type,
            'actionname': self.data.name,
            'summary': self.data.summary,
            'user': user,
            'date': datetime.utcnow().isoformat(),
            'request_uri': requri
        }
        if self.obj is not None:
            data['object'] = IUUID(self.obj)
            data['path'] = '/'.join(self.obj.getPhysicalPath())
        else:
            data['object'] = ''
            data['path'] = ''
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
            data['summary'] = 'Configuration Record %s modified. Old value: %s, New value: %s' % (
                self.event.record,
                self.event.oldValue,
                self.event.newValue
            )
        except AttributeError:
            data['summary'] = 'Configuration Record %s modified.' % self.event.record
        return data


class CacheInvalidatedRecorder(DefaultRecorder):
    def __call__(self):
        data = super(CacheInvalidatedRecorder, self).__call__()
        success = getattr(self.event, 'success', False)
        purged = getattr(self.event, 'purged', [])
        is_automatic_purge = getattr(self.event, 'is_automatic_purge', [])

        if is_automatic_purge:
            data['actionname'] += ' Automatically'
        else:
            data['actionname'] += ' Manually'
        if success:
            summary = 'The following urls have been purged: {urls}'.format(urls=repr(purged))
        else:
            summary = 'Cache invalidation failure. Make sure caching proxies are properly configured.'
        data['summary'] = summary
        return data


class ContentChangeNoteRecorder(DefaultRecorder):
    def __call__(self):
        data = super(ContentChangeNoteRecorder, self).__call__()
        data['summary'] = 'Change Note Summary: %s' % \
                          self.event.object.changeNote
        return data


class AuditData(object):
    def __init__(self, _type, name, summary=None, recorder_class=DefaultRecorder):
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
        recorder_class=ContentChangeNoteRecorder),
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
        recorder_class=CacheInvalidatedRecorder),
}


def record(success, recorder, site_path):
    if not success:
        return
    if recorder.valid:
        data = recorder()
        data["schema_version"] = "1"
        data["schema_type"] = "castle.cms.audit"
        data["instance"] = os.getenv("CASTLE_CMS_AUDIT_LOG_INSTANCE", "(not configured)")
        data["site"] = site_path
        auditlogger.info(site_path, extra=data)


def event(obj, event=None):
    if event is None:
        # some events don't include object
        event = obj
        obj = None

    interface = providedBy(event).declared[0]
    if interface not in _registered:
        return

    if obj is not None and ITrashed.providedBy(obj):
        # special handling for ITrashed...
        # we don't want to record transition events for trashing
        # and we want a special psuedo trash event
        # then, we still want an event when it gets deleted for good
        if interface not in (IAfterTransitionEvent, IObjectRemovedEvent):
            # dive out if not IAfterTransitionEvent or object removed event
            return
        if interface == IObjectRemovedEvent:
            audit_data = _registered[interface]
        else:
            audit_data = _registered[ITrashed]
    else:
        audit_data = _registered[interface]

    recorder = audit_data.get_recorder(event, obj)
    try:
        site_path = '/'.join(api.portal.get().getPhysicalPath())
    except api.exc.CannotGetPortalError:
        site_path = '(zoperoot)'
    transaction.get().addAfterCommitHook(record, args=(recorder, site_path))
