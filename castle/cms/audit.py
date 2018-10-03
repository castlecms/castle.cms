import threading
from datetime import datetime

import transaction
from castle.cms.events import IMetaTileEditedEvent
from castle.cms.interfaces import ITrashed
from castle.cms.utils import ESConnectionFactoryFactory
from elasticsearch import TransportError
from plone import api
from plone.app.iterate.interfaces import (IAfterCheckinEvent,
                                          ICancelCheckoutEvent, ICheckoutEvent,
                                          IWorkingCopyDeletedEvent)
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from Products.PluggableAuthService.interfaces.events import (ICredentialsUpdatedEvent,  # noqa
                                                             IPrincipalCreatedEvent,  # noqa
                                                             IPrincipalDeletedEvent,  # noqa
                                                             IPropertiesUpdatedEvent,  # noqa
                                                             IUserLoggedInEvent,  # noqa
                                                             IUserLoggedOutEvent)  # noqa
from zope.component import ComponentLookupError, getUtility
from zope.globalrequest import getRequest
from zope.interface import providedBy
from zope.lifecycleevent.interfaces import (IObjectAddedEvent,
                                            IObjectCopiedEvent,
                                            IObjectModifiedEvent,
                                            IObjectMovedEvent,
                                            IObjectRemovedEvent)


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
    IObjectModifiedEvent: AuditData('content', 'Modified'),
    IObjectMovedEvent: AuditData('content', 'Moved'),
    IObjectRemovedEvent: AuditData('content', 'Deleted'),
    IPrincipalCreatedEvent: AuditData('user', 'Created'),
    ITrashed: AuditData('content', 'Trashed'),
    IUserLoggedInEvent: AuditData(
        'user', 'Logged in', recorder_class=LoggedInRecorder),
    IUserLoggedOutEvent: AuditData('user', 'Logged out'),
    IPrincipalDeletedEvent: AuditData('user', 'Deleted'),
    ICredentialsUpdatedEvent: AuditData('user', 'Password updated'),
    IPropertiesUpdatedEvent: AuditData('user', 'Properties updated'),
    IAfterTransitionEvent: AuditData(
        'workflow', 'Transition', recorder_class=WorkflowRecorder),
    IMetaTileEditedEvent: AuditData(
        'slots', 'Slot edited', recorder_class=MetaTileRecorder),
}


es_doc_type = 'entry'


def _create_index(es, index_name):
    mapping = {'properties': {
        'type': {'store': False, 'type': 'string', 'index': 'not_analyzed'},
        'name': {'store': False, 'type': 'string', 'index': 'not_analyzed'},
        'summary': {'store': False, 'type': 'string', 'index': 'not_analyzed'},
        'user': {'store': False, 'type': 'string', 'index': 'not_analyzed'},
        'request_uri': {'store': False, 'type': 'string',
                        'index': 'not_analyzed'},
        'date': {'store': False, 'type': 'date'},
        'object': {'store': False, 'type': 'string', 'index': 'not_analyzed'},
        'path': {'store': False, 'type': 'string', 'index': 'not_analyzed'},
    }}
    if not es.indices.exists(index_name):
        es.indices.create(index_name)
    es.indices.put_mapping(
        doc_type=es_doc_type,
        body=mapping,
        index=index_name)


def get_index_name(site_path=None):
    if site_path is None:
        site_path = '/'.join(api.portal.get().getPhysicalPath())
    return site_path.replace('/', '').replace(' ', '').lower()


def _record(conn_factory, site_path, data):
    index_name = get_index_name(site_path)
    es = conn_factory()
    try:
        es.index(index=index_name, doc_type=es_doc_type, body=data)
    except TransportError as ex:
        if 'InvalidIndexNameException' in ex.error:
            try:
                _create_index(es, index_name)
            except TransportError:
                return
            _record(conn_factory, site_path, data)


def record(success, recorder, site_path, conn):
    if not success:
        return
    if recorder.valid:
        data = recorder()
        thread = threading.Thread(target=_record, args=(
            conn,
            site_path,
            data
        ))
        thread.start()


def event(obj, event=None):

    if event is None:
        # some events don't include object
        event = obj
        obj = None

    iface = providedBy(event).declared[0]
    if iface in _registered:
        try:
            registry = getUtility(IRegistry)
        except ComponentLookupError:
            return
        if not registry.get('collective.elasticsearch.interfaces.IElasticSettings.enabled', False):  # noqa
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
        transaction.get().addAfterCommitHook(record, args=(
            recorder, site_path, ESConnectionFactoryFactory(registry)))
    else:
        pass
