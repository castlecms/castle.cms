import logging
import types
from os import path
from time import time

from AccessControl import getSecurityManager
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms.events import AppInitializedEvent
from castle.cms.interfaces import ICastleApplication
from celery.result import AsyncResult
from collective.easyform.api import dollar_replacer
from collective.easyform.api import filter_fields
from collective.easyform.api import filter_widgets
from collective.easyform.api import get_schema
from collective.easyform.api import lnbr
from collective.easyform.api import OrderedDict
from collective.easyform.actions import DummyFormView
from collective.elasticsearch.es import CUSTOM_INDEX_NAME_ATTR
from collective.elasticsearch.es import ElasticSearchCatalog  # noqa
from OFS.CopySupport import CopyError
from OFS.CopySupport import _cb_decode
from OFS.CopySupport import _cb_encode
from OFS.CopySupport import eInvalid
from OFS.CopySupport import eNoData
from plone import api
from plone.keyring.interfaces import IKeyManager
from plone.session import tktauth
from plone.transformchain.interfaces import ITransform
from Products.CMFPlone.CatalogTool import CatalogTool
from Products.CMFPlone.utils import safe_unicode
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from ZODB.POSException import ConnectionStateError
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.event import notify
from zope.interface import implementer
from zope.schema import getFieldsInOrder

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


def patched_get_mail_body(self, unsorted_data, request, context):
    """Returns the mail-body with footer."""
    def _get_body_part(self, body_part_name):
        # pass both the bare_fields (fgFields only) and full fields.
        # bare_fields for compatability with older templates,
        # full fields to enable access to htmlValue
        if isinstance(self.__getattribute__(body_part_name), basestring):  # noqa:F821
            return self.__getattribute__(body_part_name)
        else:
            return self.__getattribute__(body_part_name).output

    def _do_dollar_replacement(self, body_part, data):
        return body_part and lnbr(dollar_replacer(body_part, data))

    def _get_fields_dict(fields_in_order):
        return OrderedDict([
            (i, j.title)
            for i, j in fields_in_order
        ])

    def _get_label_fields(fields_in_order):
        return [
            field_name for field_name, field in fields_in_order
            if 'label' in type(field).__name__.lower()
        ]

    def _get_body_pt_file():
        this_path = path.dirname(__file__)
        template_path = path.join(
            this_path,
            'easyform',
            "override_mail_body_default.pt"
        )
        return safe_unicode(
            open(template_path).read()
        )

    def _get_updated_form(schema, context, request):
        form = DummyFormView(context, request)
        form.schema = schema
        form.prefix = 'form'
        form._update()
        return form

    def _get_body_parts(self):
        return (
            self._get_body_part('body_pre'),
            self._get_body_part('body_post'),
            self._get_body_part('body_footer'),
        )

    def _get_template(self, context):
        template = ZopePageTemplate(self.__name__)
        template.write(self.body_pt)
        return template.__of__(context)

    def _add_methods_to_mailer_instance(mailer):
        mailer._get_body_part = types.MethodType(_get_body_part, mailer)
        mailer._get_body_parts = types.MethodType(_get_body_parts, mailer)
        mailer._do_dollar_replacement = types.MethodType(_do_dollar_replacement, mailer)
        mailer._get_template = types.MethodType(_get_template, mailer)

    _add_methods_to_mailer_instance(self)
    self.body_pt = _get_body_pt_file()

    schema = get_schema(context)
    form = _get_updated_form(schema, context, request)
    widgets = filter_widgets(self, form.w)
    data = filter_fields(self, schema, unsorted_data)
    body_pre, body_post, body_footer = _get_body_parts(self)
    fields_in_order = getFieldsInOrder(schema)
    extra = {
        'data': data,
        'fields': _get_fields_dict(fields_in_order),
        'label_fields': _get_label_fields(fields_in_order),
        'widgets': widgets,
        'mailer': self,
        'body_pre': self._do_dollar_replacement(body_pre, data),
        'body_post': self._do_dollar_replacement(body_post, data),
        'body_footer': self._do_dollar_replacement(body_footer, data),
    }
    template = self._get_template(context)
    return template.pt_render(extra_context=extra)


# AsyncResult objects have a memory leak in them in Celery 4.2.1.
# See https://github.com/celery/celery/pull/4839/
if hasattr(AsyncResult, '__del__'):
    delattr(AsyncResult, '__del__')
