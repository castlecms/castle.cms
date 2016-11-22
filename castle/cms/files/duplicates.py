from BTrees.OOBTree import OOBTree
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.uuid.interfaces import IUUID
from zope.annotation.interfaces import IAnnotations


DATA_KEY = 'castle.cms.filehashes'


class DuplicateDetector(object):

    def __init__(self):
        self.site = api.portal.get()
        self.annotations = IAnnotations(self.site)
        self.data = self.annotations.get(DATA_KEY)

    def register(self, obj, hash):
        if self.data is None:
            self.annotations[DATA_KEY] = OOBTree()
            self.data = self.annotations[DATA_KEY]
        self.data[hash] = IUUID(obj)

    def get_object(self, hash):
        if self.data is None:
            return None
        if hash not in self.data:
            return None
        uuid = self.annotations[DATA_KEY][hash]
        return uuidToObject(uuid)


class DuplicateException(Exception):

    def __init__(self, obj):
        self.obj = self.object = self.context = obj
        self.message = 'File already found'
