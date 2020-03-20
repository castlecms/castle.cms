from castle.cms import trash
from castle.cms.interfaces import ITrashed
from castle.cms.constants import TRASH_LOG_KEY
from plone import api
from plone.app.linkintegrity.exceptions import LinkIntegrityNotificationException
from plone.locking.interfaces import ILockable
from zope.annotation.interfaces import IAnnotations
from Products.Five import BrowserView
from unidecode import unidecode
from zope.event import notify
from castle.cms.events import TrashEmptiedEvent

import json


class TrashView(BrowserView):

    def __call__(self):
        self.catalog = api.portal.get_tool('portal_catalog')
        self.site = api.portal.get()
        self.site_path = '/'.join(self.site.getPhysicalPath())
        if self.request.REQUEST_METHOD == 'POST':
            action = self.request.get('action')
            if action == 'restore':
                self.restore()
            elif action == 'delete':
                self.delete()
            elif action == 'empty':
                self.empty()
        self.items = self.catalog(trashed=True, sort_on='modified',
                                  sort_order='reverse',
                                  object_provides=ITrashed.__identifier__)
        return self.index()

    def get_label(self, brain):
        label = brain.Title
        if brain.is_folderish:
            num = len(self.catalog(trashed=True,
                                   path={'query': brain.getPath(), 'depth': -1}))
            label += '(%i items)' % num
        return label

    def get_path(self, brain):
        if hasattr(brain, 'getPath'):
            path = brain.getPath()
        else:
            path = '/'.join(brain.getPhysicalPath())
        return path[len(self.site_path):]

    def get_by_uid(self, uid):
        return self.catalog(UID=uid, trashed=True)[0].getObject()

    # used for modifying the location in a IStatusMessage
    # if we need this for something else we can move it to a static function library
    def _special_IStatusMessage_fmt(self, text, location):
        return unicode(json.dumps({
            'text': text,
            'location': location,
            # the JS handles this special case here:
            # https://github.com/castlecms/castle.cms
            # /blob/9e6ea3a4a6dcd07b28cc39b2e950b21e6e2d3d81/castle/cms/static/patterns/toolbar.js#L554
            'parseAsJSON': True
        }), 'utf-8')

    # wrapper for _special_IStatusMessage_fmt and api.portal.show_message
    def send_IStatusMessage_info_with_location(self, text, location):
        api.portal.show_message(self._special_IStatusMessage_fmt(text, location), self.request, type='info')

    def restore(self):
        uid = self.request.get('uid')
        obj = self.get_by_uid(uid)
        self.send_IStatusMessage_info_with_location('Successfully restored: ' + unidecode(obj.Title()), self.get_path(obj))
        trash.restore(obj)

    def delete(self):
        obj = self.get_by_uid(self.request.get('uid'))
        lockable = ILockable(obj, None)
        if lockable and lockable.locked():
            lockable.clear_locks()
        try:
            api.content.delete(obj)
            api.portal.show_message('Successfully deleted "%s" located at: %s' % (
                unidecode(obj.Title()), self.get_path(obj)), self.request, type='warning')
        except LinkIntegrityNotificationException:
            api.portal.show_message('Can not delete "%s" located at: %s because it is still linked.' % (
                unidecode(obj.Title()), self.get_path(obj)), self.request, type='warning')

    def empty(self):
        for item in [i for i in self.catalog(trashed=True,
                                             object_provides=ITrashed.__identifier__)]:
            obj = item.getObject()
            lockable = ILockable(obj, None)
            if lockable and lockable.locked():
                lockable.clear_locks()
            try:
                api.content.delete(obj, check_linkintegrity=False)
            except LinkIntegrityNotificationException:
                # could be a folder that has been deleted
                api.portal.show_message(
                    'Some content could not be removed because it is still linked '
                    'to other content on the site.',
                    self.request, type='warning')
        notify(TrashEmptiedEvent(self))
        api.portal.show_message('Trash emptied', self.request, type='warning')

    def get_trash_log(self):
        annotations = IAnnotations(self.site)
        if TRASH_LOG_KEY in annotations:
            return annotations[TRASH_LOG_KEY]
        else:
            return "No empty operation log, the trash has not been emptied"
