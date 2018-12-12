from plone.registry.interfaces import IRegistry
from castle.cms.interfaces import ICrawlerConfiguration
from zope.component import getUtility

import logging
log = logging.getLogger(__name__)

PROFILE_ID = 'profile-castle.cms.upgrades:2_3_5'


def upgrade(context, logger=None):
    registry = getUtility(IRegistry)
    crawler_settings = registry.forInterface(ICrawlerConfiguration,
                                                prefix='castle')
    try:
        interval = crawler_settings.crawler_interval
    except Exception:
        interval = 0
    crawler_settings.crawler_interval = interval
