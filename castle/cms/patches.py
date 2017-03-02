from AccessControl import getSecurityManager
from Acquisition import aq_parent
from castle.cms import authentication
from castle.cms import cache
from castle.cms.interfaces import ICastleApplication
from collective.elasticsearch.es import ElasticSearchCatalog  # noqa
from OFS.CopySupport import _cb_decode
from OFS.CopySupport import _cb_encode
from OFS.CopySupport import CopyError
from OFS.CopySupport import eInvalid
from OFS.CopySupport import eNoData
from plone import api
from plone.keyring.interfaces import IKeyManager
from plone.namedfile.interfaces import INamedField
from plone.rfc822.interfaces import IPrimaryFieldInfo
from plone.session import tktauth
from plone.transformchain.interfaces import ITransform
from time import time
from ZODB.POSException import POSKeyError
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.interface import implementer


def HideSiteLayoutFields_update(self):
    """
    we don't want to hide these fields
    """
    return


def MosaicRegistry_parseRegistry(self):
    cache_key = '%s-mosaic-registry' % '/'.join(api.portal.get().getPhysicalPath()[1:])
    try:
        return cache.get(cache_key)
    except KeyError:
        result = self._old_parseRegistry()
        cache.set(cache_key, result, 60 * 2)  # cache for 2 minutes
        return result


if not hasattr(ElasticSearchCatalog, 'original_searchResults'):
    ElasticSearchCatalog.original_searchResults = ElasticSearchCatalog.searchResults
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
    except:
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
    authentication.install_acl_users(app, self.commit)


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
    return ticket_data
