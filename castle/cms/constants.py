from collections import namedtuple

from castle.cms.package import CASTLE_VERSION  # noqa:F401
from castle.cms.package import CASTLE_VERSION_STRING  # noqa:F401
from re import compile

SHIELD = namedtuple('SHIELD', 'NONE BACKEND ALL')('', 'backend', 'all')
MAX_PASTE_ITEMS = 40
ALL_SUBSCRIBERS = '--SUBSCRIBERS--'
ALL_USERS = '--USERS--'
DEFAULT_SITE_LAYOUT_REGISTRY_KEY = 'castle.cms.mosaic.default_site_layout'
CRAWLED_SITE_ES_DOC_TYPE = 'website'
CRAWLED_DATA_KEY = 'castle.cms.crawldata'
TRASH_LOG_KEY = 'castle.cms.empty-trash-log'
ANONYMOUS_USER = "Anonymous User"
DEFAULT_FONT_SIZE_SMALL = u'12pt'
DEFAULT_FONT_SIZE_MEDIUM = u'14pt'
DEFAULT_FONT_SIZE_LARGE = u'16pt'
ABSOLUTE_FONT_UNITS = (
    'cm',
    'mm',
    'Q',
    'in',
    'pc',
    'pt',
    'px',
)
VALID_CSS_FONT_SIZE_PATTERN = compile("^\s*\d+\s*({})\s*$".format(  # noqa:W605
    '|'.join(ABSOLUTE_FONT_UNITS)
))
