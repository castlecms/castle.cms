from . import cloudflare
from . import varnish
from castle.cms.interfaces import ICastleThemingCacheReset
from castle.cms.cache import get_client
from castle.cms.cache import ram
from castle.cms.cache import redis_installed
from plone.app.theming.policy import ThemingPolicy
from plone.app.theming.utils import getZODBThemes
from plone.app.theming.utils import getAvailableThemes
from logging import getLogger
from zope.component import getUtility
from zope.interface import implementer
from ZODB.Connection import resetCaches
import transaction

logger = getLogger(__name__)


@implementer(ICastleThemingCacheReset)
class CastleCmsThemingCacheReset(ThemingPolicy):

    def invalidateOtherCaches(self):
        self._reset_other_cache()
        self.invalidateCache()

    def _reset_other_cache(self):
        """
         Clears out the redis cache, the ramcache.
         And ZODB cache as well
        """

        if redis_installed() is not False:
            try:
                logger.info("Resetting redis cache")
                redis = get_client()
                redis.reset()
            except Exception as ex:
                logger.warning("Something went wrong with the redis cache reset %s" % ex)
        else:
            logger.info("Redis not installed, skipping redis cache reset")

        try:
            logger.info("Resetting ram cache")
            ram.reset()
        except Exception as ex:
            logger.warning("Something went wrong with reseting the ram cache. %s" %ex)

        try:
            if getZODBThemes() == []:
                pass
            else:
                logger.info("Resetting ZODB cache")
                resetCaches()
        except Exception as ex:
            logger.warning("Something went wrong with ZODB resetCaches()" \
                           "%s" % ex)

        try:
            purger = cloudflare.get()
            if purger.enabled:
                logger.info("Resetting Cloudfare Cache")
                purger.purge_themes()
            else:
                logger.info("Cloudfare is not enabled, " \
                            "if it is meant to be enabled please check the CastleCMS cloudfare settings")
        except Exception as ex:
            logger.info("Unable to reset Cloudfare Cache %s" %ex)

        try:
            purger = varnish.get()
            if(purger.enabled):
                logger.info("Resetting Varnish Cache")
                purger.purge_themes()
            else:
                logger.info("Varnish is not enabled, " \
                            "If it is meant to be enabled please check the CastleCMS varnish settings")
        except Exception as ex:
            logger.info("Unable to reset Varnish Cache %s" %ex)
