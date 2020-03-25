from castle.cms.cache import get_client
from castle.cms.cache import ram
from castle.cms.cache import redis_installed
from logging import getLogger
from ZODB.Connection import Connection

logger = getLogger(__name__)

class CastleCmsThemingCacheReset(object):

    def invalidateCache(self):
        self._reset_local_cache()
    
    def _reset_local_cache(self):
        """
         Clears out the redis cache, the ramcache.
         And ZODB cache as well
        """

        if redis_installed() is not False:
            logger.info("Resetting redis cache")
            redis = get_client()
            redis.reset()
        else:
            logger.info("Redis not installed, skipping redis cache reset")

        logger.info("Resetting ram cache")
        ram.reset()

        logger.info("Resetting ZODB cache")
        
        Connection.cacheMinimize()
