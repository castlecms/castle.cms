from . import cloudflare
from castle.cms.cache import get_client
from castle.cms.cache import ram
from castle.cms.cache import redis_installed
from plone.app.theming.utils import getZODBThemes
from plone.app.theming.utils import getAvailableThemes
from logging import getLogger
from zope.component import getUtility
from ZODB.Connection import resetCaches
import transaction

logger = getLogger(__name__)

class CastleCmsThemingCacheReset(object):

    def invalidateCache(self):
        import pdb; pdb.set_trace()
        self._reset_other_cache()
    
    def _reset_other_cache(self):
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
        
        try:
            if getZODBThemes() == []:
                logger.info("No Themes in ZODB Skipping")
            else:
                resetCaches()
        except Exception as ex:
            logger.warning("Something went wrong with ZODB resetCaches()" \
            "%s" % ex)

        logger.info("Resetting Cloudfare Cache")
        try:
            purger = cloudflare.get()
            purger.purge_themes()
            if purger.enabled:
                pass
            else:
                logger.info("Cloudfare is not enabled, "
                "if it is meant to be enabled please check the CastleCMS cloudfare settings")
        except:
            logger.info("Unable to reset Cloudfare Cache")
        
        
