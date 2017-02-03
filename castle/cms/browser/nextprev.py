from AccessControl import getSecurityManager
from Acquisition import aq_parent
from castle.cms.interfaces import ITrashed
from plone import api
from plone.app.dexterity.behaviors.nextprevious import NextPreviousBase
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces._content import IFolderish
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from zope.component import getUtility


class NextPrevious(NextPreviousBase):

    def __init__(self, context):
        if not IFolderish.providedBy(context):
            # need to be able to drop on page as well
            context = aq_parent(context)

        self.context = context
        registry = getUtility(IRegistry)
        self.vat = registry.get('plone.types_use_view_action_in_listings', [])
        self.security = getSecurityManager()
        if IPloneSiteRoot.providedBy(context):
            catalog = api.portal.get_tool('portal_catalog')
            folder_path = '/'.join(context.getPhysicalPath())
            brains = catalog(path={'query': folder_path, 'depth': 1})
            order = [b.id for b in brains]
        else:
            order = context.getOrdering()
            if not isinstance(order, list):
                order = order.idsInOrder()
            if not isinstance(order, list):
                order = None
        self.order = order

    def getNextItem(self, obj):
        """ return info about the next item in the container """
        if not self.order:
            return None
        try:
            pos = self.order.index(obj.getId())
        except ValueError:
            return
        for oid in self.order[pos + 1:]:
            data = self.getData(self.context[oid])
            if data:
                return data

    def getData(self, obj):
        if ITrashed.providedBy(obj):
            return None
        data = super(NextPrevious, self).getData(obj)
        if data:
            data['obj'] = obj
        return data
