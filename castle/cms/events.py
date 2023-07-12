from zope.interface import implementer
from zope.component.interfaces import ObjectEvent, IObjectEvent


class IMetaTileEditedEvent(IObjectEvent):
    pass


class MetaTileEvent(ObjectEvent):
    def __init__(self, object, tile_id, **descriptions):
        super(MetaTileEvent, self).__init__(object, **descriptions)
        self.tile_id = tile_id


@implementer(IMetaTileEditedEvent)
class MetaTileEditedEvent(MetaTileEvent):
    pass


class IAppInitializedEvent(IObjectEvent):
    pass


@implementer(IAppInitializedEvent)
class AppInitializedEvent(ObjectEvent):
    def __init__(self, object, commit):
        super(AppInitializedEvent, self).__init__(object)
        self.commit = commit


class ITrashEmptiedEvent(IObjectEvent):
    pass


@implementer(ITrashEmptiedEvent)
class TrashEmptiedEvent(ObjectEvent):
    def __init__(self, object):
        super(TrashEmptiedEvent, self).__init__(object)


class ICacheInvalidatedEvent(IObjectEvent):
    pass


@implementer(ICacheInvalidatedEvent)
class CacheInvalidatedEvent(ObjectEvent):
    def __init__(self, object, success=False, purged=None, is_automatic_purge=False):
        if purged is None:
            purged = []
        super(CacheInvalidatedEvent, self).__init__(object)
        self.success = success
        self.purged = purged
        self.is_automatic_purge = is_automatic_purge
