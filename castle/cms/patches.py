import logging
from six import iteritems as six_iteritems
from time import time

from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms.constants import CASTLE_VERSION_STRING
from castle.cms.events import AppInitializedEvent
from castle.cms.interfaces import ICastleApplication
from celery.result import AsyncResult
from collective.elasticsearch.es import CUSTOM_INDEX_NAME_ATTR
from collective.elasticsearch.es import ElasticSearchCatalog  # noqa
from OFS.CopySupport import CopyError
from OFS.CopySupport import _cb_decode
from OFS.CopySupport import _cb_encode
from OFS.CopySupport import eInvalid
from OFS.CopySupport import eNoData
from plone.app.widgets.base import dict_merge
from plone.app.widgets.utils import get_tinymce_options
from plone.app.z3cform.widget import RichTextWidget
from plone.dexterity.utils import resolveDottedName
from plone.keyring.interfaces import IKeyManager
from plone.session import tktauth
from plone.transformchain.interfaces import ITransform
from Products.CMFPlone.CatalogTool import CatalogTool
from Products.CMFPlone.resources import add_resource_on_request
from ZODB.POSException import ConnectionStateError
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.event import notify
from zope.interface import implementer

import plone.api as api


logger = logging.getLogger('castle.cms')


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


def es_custom_index(self, catalogtool):
    es_index_enabled = api.portal.get_registry_record('castle.es_index_enabled', default=False)
    if es_index_enabled:
        new_index = api.portal.get_registry_record('castle.es_index')
        setattr(CatalogTool, CUSTOM_INDEX_NAME_ATTR, new_index)
    else:
        try:
            delattr(CatalogTool, CUSTOM_INDEX_NAME_ATTR)
        except AttributeError:
            pass

    self._old___init__(catalogtool)


def version_overview(self):
    return [CASTLE_VERSION_STRING] + self._old_version_overview()


def rich_text_args(self):
    args = super(RichTextWidget, self)._base_args()
    args['name'] = self.name
    value = self.value and self.value.raw_encoded or ''
    args['value'] = (self.request.get(
        self.field.getName(), value)).decode('utf-8')
    args.setdefault('pattern_options', {})

    # displays tinymce editor for anonymous users
    if api.user.is_anonymous():
        add_resource_on_request(self.request, 'mockup-patterns-tinymce-logged-out')

    merged_options = dict_merge(get_tinymce_options(self.context,
                                                    self.field,
                                                    self.request),  # noqa
                                args['pattern_options'])
    args['pattern_options'] = merged_options

    return args


# If a behavior provides an image field (or, probably, file or similar large blobby thing),
# and data is stored for that field, then there's a whole complicated set of things that happen
# to try to not store a copy of the blob, but instead a reference to it, as long as it hasn't changed.
# this is perfectly reasonable. this data is retrieved in Products.CMFEditions as referenced_data,
# a dict that has as keys the dotted names of interfaces (which again, can come from a behavior)
# this method here, then, after doing some incomprehensible stuff, attempts to use those interfaces
# to look up fields and then adapt them, which will fail if the dexterity object no longer provides
# that interface (due to, for example, a behavior being removed). This patch attempts to bypass the
# part of the code that will fail if the interface is no longer provided.
def reattachReferencedAttributes(self, obj, attributes_dict):
    obj = aq_base(obj)
    for name, blob in six_iteritems(attributes_dict):
        interface = resolveDottedName('.'.join(name.split('.')[:-1]))
        if interface.providedBy(obj):  # Interface may have come from now-deactivated behavior or similar
            field_name = name.split('.')[-1]
            field = interface.get(field_name)
            if field is not None:  # Field may have been removed from schema
                adapted_field = field.get(interface(obj))
                if adapted_field:
                    adapted_field._blob = blob


# AsyncResult objects have a memory leak in them in Celery 4.2.1.
# See https://github.com/celery/celery/pull/4839/
if getattr(AsyncResult, '__del__', False):
    delattr(AsyncResult, '__del__')
