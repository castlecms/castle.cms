import logging
import six
from time import time

from AccessControl import getSecurityManager
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import search_zcatalog as SearchZCatalog
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms.events import AppInitializedEvent
from castle.cms.interfaces import ICastleApplication
from celery.result import AsyncResult
from collective.elasticsearch.es import ElasticSearchCatalog  # noqa
from DateTime import DateTime
from OFS.CopySupport import CopyError
from OFS.CopySupport import _cb_decode
from OFS.CopySupport import _cb_encode
from OFS.CopySupport import eInvalid
from OFS.CopySupport import eNoData
from plone.keyring.interfaces import IKeyManager
from plone.registry.interfaces import IRegistry
from plone.session import tktauth
from plone.transformchain.interfaces import ITransform
from ZODB.POSException import ConnectionStateError
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.event import notify
from zope.interface import implementer
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.ZCatalog.ZCatalog import ZCatalog
from zope.component import getUtility

logger = logging.getLogger('castle.cms')
security = ClassSecurityInfo()

@security.protected(SearchZCatalog)
def private_parents_search_results(self, REQUEST=None, **kw):

    kw = kw.copy()
    show_inactive = kw.get('show_inactive', False)
    if isinstance(REQUEST, dict) and not show_inactive:
        show_inactive = 'show_inactive' in REQUEST

    user = _getAuthenticatedUser(self)
    kw['allowedRolesAndUsers'] = self._listAllowedRolesAndUsers(user)

    if not show_inactive \
        and not _checkPermission(AccessInactivePortalContent, self):
        kw['effectiveRange'] = DateTime()

    registry = getUtility(IRegistry)
    if not registry.get('plone.allow_public_in_private_container', False):
        kw['has_private_parents'] = False
        
    # filter out invalid sort_on indexes
    sort_on = kw.get('sort_on') or []
    if isinstance(sort_on, six.string_types):
        sort_on = [sort_on]
    valid_indexes = self.indexes()
    try:
        sort_on = [idx for idx in sort_on if idx in valid_indexes]
    except TypeError:
        # sort_on is not iterable
        sort_on = []
    if not sort_on:
        kw.pop('sort_on', None)
    else:
        kw['sort_on'] = sort_on

    return ZCatalog.searchResults(self, REQUEST, **kw)



def HideSiteLayoutFields_update(self):
    """
    we don't want to hide these fields
    """
    return


if not hasattr(ElasticSearchCatalog, 'original_searchResults'):
    ElasticSearchCatalog.original_searchResults = ElasticSearchCatalog.searchResults  # noqa

    def searchResultsTrashed(self, REQUEST=None, check_perms=False, **kw):
        if 'trashed' not in kw:
            kw['trashed'] = False
        return self.original_searchResults(REQUEST, check_perms, **kw)
    ElasticSearchCatalog.searchResults = searchResultsTrashed


def Content_addCreator(self, creator=None):
    """ Add creator to Dublin Core creators.
    """
    if len(self.creators) > 0:
        # do not add creator if one is already set
        return

    if creator is None:
        user = getSecurityManager().getUser()
        creator = user and user.getId()

    # call self.listCreators() to make sure self.creators exists
    if creator and creator not in self.listCreators():
        self.creators = self.creators + (creator, )


def manage_pasteObjects(self, cb_copy_data=None, REQUEST=None):
    """
    override normal paste action to see if we're looking at the paste
    data being stored in cache
    """
    if cb_copy_data is not None:
        cp = cb_copy_data
    elif REQUEST is not None and '__cp' in REQUEST:
        cp = REQUEST['__cp']
    else:
        cp = None
    if cp is None:
        raise CopyError(eNoData)

    try:
        op, mdatas = _cb_decode(cp)
    except Exception:
        raise CopyError(eInvalid)

    try:
        if mdatas[0][0].startswith('cache:'):
            cache_key = mdatas[0][0].replace('cache:', '')
            new_mdatas = cache.get(cache_key)
            cdata = _cb_encode((op, new_mdatas))
            return self._old_manage_pasteObjects(cdata)
    except IndexError:
        pass
    return self._old_manage_pasteObjects(cb_copy_data, REQUEST)


@implementer(ITransform)
class NoopTransform(object):

    order = 8800

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def transformString(self, result, encoding):
        return None
    transformUnicode = transformIterable = transformString


def AppInitializer_initialize(self):
    self._old_initialize()
    app = self.app[0]
    notify(AppInitializedEvent(app, self.commit))


def SessionPlugin_validateTicket(self, ticket, now=None):
    if now is None:
        now = time()
    if self._shared_secret is not None:
        ticket_data = tktauth.validateTicket(
            self._shared_secret,
            ticket,
            timeout=self.timeout,
            now=now,
            mod_auth_tkt=self.mod_auth_tkt
        )
    else:
        ticket_data = None
        parent = aq_parent(aq_parent(self))

        is_root = ICastleApplication.providedBy(parent)
        if is_root:
            manager = getGlobalSiteManager().queryUtility(IKeyManager)
        else:
            manager = queryUtility(IKeyManager)

        if manager is None:
            return None

        try:
            for secret in manager[u"_system"]:
                if secret is None:
                    continue
                ticket_data = tktauth.validateTicket(
                    secret,
                    ticket,
                    timeout=self.timeout,
                    now=now,
                    mod_auth_tkt=self.mod_auth_tkt
                )
                if ticket_data is not None:
                    break
        except ConnectionStateError:
            logger.warning(
                'Connection state error, swallowing', exc_info=True)
    return ticket_data


# AsyncResult objects have a memory leak in them in Celery 4.2.1.
# See https://github.com/celery/celery/pull/4839/
if hasattr(AsyncResult, '__del__'):
    delattr(AsyncResult, '__del__')
