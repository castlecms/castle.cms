import logging
from time import time

from AccessControl import getSecurityManager
from Acquisition import aq_parent
from castle.cms import authentication
from castle.cms import cache
from castle.cms.interfaces import ICastleApplication
from castle.cms.tiles.dynamic import get_tile_manager
from celery.result import AsyncResult
from collective.elasticsearch.es import ElasticSearchCatalog  # noqa
from OFS.CopySupport import CopyError
from OFS.CopySupport import _cb_decode
from OFS.CopySupport import _cb_encode
from OFS.CopySupport import eInvalid
from OFS.CopySupport import eNoData
from plone import api
from plone.keyring.interfaces import IKeyManager
from plone.registry.interfaces import IRegistry
from plone.session import tktauth
from plone.transformchain.interfaces import ITransform
from Products.CMFPlone.interfaces import ITinyMCESchema
from ZODB.POSException import ConnectionStateError
from zope.component import getGlobalSiteManager
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import implementer


logger = logging.getLogger('castle.cms')


MOSAIC_CACHE_DURATION = 1 * 60


def HideSiteLayoutFields_update(self):
    """
    we don't want to hide these fields
    """
    return


_rich_text_widget_types = (
    'plone_app_z3cform_wysiwyg_widget_WysiwygWidget',
    'plone_app_z3cform_wysiwyg_widget_WysiwygFieldWidget',
    'plone_app_widgets_dx_RichTextWidget',
    'plone_app_z3cform_widget_RichTextFieldWidget',

)


def MosaicRegistry_parseRegistry(self):
    cache_key = '%s-mosaic-registry' % '/'.join(
        api.portal.get().getPhysicalPath()[1:])
    if not api.env.debug_mode():
        try:
            return cache.get(cache_key)
        except KeyError:
            result = self._old_parseRegistry()
    else:
        result = self._old_parseRegistry()

    mng = get_tile_manager()
    for tile in mng.get_tiles():
        key = 'castle_cms_dynamic_{}'.format(tile['id'])
        result['plone']['app']['mosaic']['app_tiles'][key] = {
            'category': tile['category'],
            'default_value': None,
            'favorite': False,
            'label': tile['title'],
            'name': tile['name'],
            'tile_type_id': u'castle.cms.dynamic',
            'read_only': False,
            'rich_text': False,
            'settings': True,
            'tile_type': u'app',
            'weight': tile['weight']
        }

    registry = getUtility(IRegistry)
    settings = registry.forInterface(
        ITinyMCESchema, prefix="plone", check=False)
    if settings.libraries_spellchecker_choice != 'AtD':
        cache.set(cache_key, result, MOSAIC_CACHE_DURATION)
        return result

    # add atd config to toolbar dynamically
    mos_settings = result['plone']['app']['mosaic']
    mos_settings['richtext_toolbar']['AtD'] = {
        'category': u'actions',
        'name': u'toolbar-AtD',
        'weight': 0,
        'favorite': False,
        'label': u'After the deadline',
        'action': u'AtD',
        'icon': False
    }
    for widget_type in _rich_text_widget_types:
        mos_settings['widget_actions'][widget_type]['actions'].append('toolbar-AtD')  # noqa
    mos_settings['structure_tiles']['text']['available_actions'].append('toolbar-AtD')  # noqa
    mos_settings['app_tiles']['plone_app_standardtiles_rawhtml']['available_actions'].append('toolbar-AtD')  # noqa
    cache.set(cache_key, result, MOSAIC_CACHE_DURATION)
    return result


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
