from castle.cms.interfaces import ITrashed
from plone import api
from plone.app.standardtiles import common
from plone.locking.browser.info import LockInfoViewlet
from plone.locking.interfaces import ITTWLockable
from plone.tiles import Tile
from zope.security import checkPermission


class LockInfoTile(Tile):
    def __call__(self):
        if checkPermission("cmf.ModifyPortalContent", self.context) and \
           ITTWLockable.providedBy(self.context):
            viewlet = LockInfoViewlet(self.context, self.request, None, None)
            return viewlet.render()


class GlobalStatusMessageTile(common.GlobalStatusMessageTile):

    def __call__(self):
        # we're overriding so we can provide extra status messages
        # just an easy way to hook in
        if ITrashed.providedBy(self.context):
            # warn user they are in no-no land
            api.portal.show_message(
                'You are viewing content that is in the recycling bin. '
                'You are still free to view and manage this object '
                'before it is restored or deleted.',
                request=self.request, type='error')
        return super(GlobalStatusMessageTile, self).__call__()
