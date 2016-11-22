from castle.cms.interfaces import ITrashed
from plone.app.dexterity.behaviors.nextprevious import NextPreviousBase


class NextPrevious(NextPreviousBase):

    def getData(self, obj):
        if ITrashed.providedBy(obj):
            return None
        data = super(NextPrevious, self).getData(obj)
        if data:
            data['obj'] = obj
        return data
