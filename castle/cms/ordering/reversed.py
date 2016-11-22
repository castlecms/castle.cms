from plone.folder.default import DefaultOrdering


class ReversedOrdering(DefaultOrdering):
    """return reversed ids."""

    def notifyAdded(self, obj_id):
        """ see interfaces.py """
        order = self._order(True)
        order.insert(0, obj_id)

    def notifyRemoved(self, obj_id):
        """ see interfaces.py """
        order = self._order()
        idx = order.index(obj_id)
        del order[idx]

    def getObjectPosition(self, obj_id):
        """ see interfaces.py """
        order = self._order()
        if obj_id in order:
            return order.index(obj_id)
        raise ValueError('No object with id "{0:s}" exists.'.format(obj_id))

    def _pos(self, create=False):
        # XXX bbb here so super class has something to use
        # I don't understand why we store the order separate
        # from the list of ids when the list of ids is also ordered
        return {}
