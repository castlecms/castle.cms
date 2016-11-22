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
