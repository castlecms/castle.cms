from castle.cms.cache import get_client
from castle.cms.cache import ram
from ZODB.Connection.Connection import cacheMinimize

@implementer(ThemingPolicy)
class CastleCmsThemingCacheReset(object):

    def _reset_local_cache(self):
        # Clears out the redis cache, the ramcache.
        # And ZODB cache as well
        import pdb; pdb.set_trace()
        redis = get_client()
            
        pass
