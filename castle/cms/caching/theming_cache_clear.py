from castle.cms.cache import get_client
from castle.cms.cache import ram
from plone.app.theming.policy import ThemingPolicy
from plone.app.theming.interfaces import IThemingPolicy
from zope.interface import implementer
#from ZODB.Connection.Connection import cacheMinimize

@implementer(IThemingPolicy)
class CastleCmsThemingCacheReset(object):

    def invalidateCache(self):
        import pdb; pdb.set_trace()
    
    def _reset_local_cache(self):
        """
         Clears out the redis cache, the ramcache.
         And ZODB cache as well
        """
        import pdb; pdb.set_trace()
        redis = get_client()
#        cacheMinimize()
