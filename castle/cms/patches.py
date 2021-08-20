import logging
from time import time

from AccessControl import getSecurityManager
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
from plone import api
from plone.keyring.interfaces import IKeyManager
from plone.session import tktauth
from plone.transformchain.interfaces import ITransform
from Products.CMFPlone.CatalogTool import CatalogTool
from ZODB.POSException import ConnectionStateError
from zope.component import getGlobalSiteManager
from zope.component import queryUtility
from zope.event import notify
from zope.interface import implementer


#! Imports for rich text widget

from Acquisition import ImplicitAcquisitionWrapper
from lxml import etree
from plone.app.textfield.value import RichTextValue
from plone.app.widgets.base import TextareaWidget
from plone.app.widgets.base import dict_merge
from plone.app.widgets.utils import get_tinymce_options
from plone.app.z3cform.utils import closest_content
import json
from plone.app.z3cform.widget import BaseWidget
from plone.app.textfield.widget import RichTextWidget as patextfield_RichTextWidget
from plone.app.z3cform.interfaces import IRichTextWidget
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IEditingSchema
from Products.CMFPlone.resources import add_resource_on_request
from UserDict import UserDict
from zope.component import getUtility
from zope.interface import implementsOnly





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


class RichTextWidget(BaseWidget, patextfield_RichTextWidget):
    _base = TextareaWidget
    implementsOnly(IRichTextWidget)
    pattern_options = BaseWidget.pattern_options.copy()

    def __init__(self, *args, **kwargs):
        super(RichTextWidget, self).__init__(*args, **kwargs)
        if api.user.is_anonymous():
            add_resource_on_request(self.request, 'mockup-patterns-tinymce-logged-out')
        self._pattern = None

    def wrapped_context(self):
        context = self.context
        content = closest_content(context)
        if context.__class__ == dict:
            context = UserDict(self.context)
        return ImplicitAcquisitionWrapper(context, content)

    @property
    def pattern(self):
        """dynamically grab the actual pattern name so it will
           work with custom visual editors"""
        if self._pattern is None:
            registry = getUtility(IRegistry)
            try:
                records = registry.forInterface(IEditingSchema, check=False,
                                                prefix='plone')
                default = records.default_editor.lower()
                available = records.available_editors  #['TinyMCE', 'None']
            except AttributeError:
                default = 'tinymce'
                available = ['TinyMCE']
            tool = getToolByName(self.wrapped_context(), "portal_membership")
            member = tool.getAuthenticatedMember()
            editor = member.getProperty('wysiwyg_editor')
            if editor in available:
                return default
            elif editor in ('None', None):
                return default
            return default
        return self._pattern

    def _base_args(self):
        args = super(RichTextWidget, self)._base_args()
        args['name'] = self.name
        value = self.value and self.value.raw_encoded or ''
        args['value'] = (self.request.get(
            self.field.getName(), value)).decode('utf-8')

        args.setdefault('pattern_options', {})
        merged_options = dict_merge(get_tinymce_options(self.context,
                                                        self.field,
                                                        self.request),  # noqa
                                    args['pattern_options'])
        args['pattern_options'] = merged_options

        return args

    def render(self):
        """Render widget.
        :returns: Widget's HTML.
        :rtype: string
        """
        if self.mode != 'display':
            # MODE "INPUT"
            rendered = ''
            allowed_mime_types = self.allowedMimeTypes()
            if not allowed_mime_types or len(allowed_mime_types) <= 1:
                # Display textarea with default widget
                rendered = super(RichTextWidget, self).render()
            else:
                # Let pat-textarea-mimetype-selector choose the widget

                # Initialize the widget without a pattern
                base_args = self._base_args()
                pattern_options = base_args['pattern_options']
                del base_args['pattern']
                del base_args['pattern_options']
                textarea_widget = self._base(None, None, **base_args)
                textarea_widget.klass = ''
                mt_pattern_name = '{}{}'.format(
                    self._base._klass_prefix,
                    'textareamimetypeselector'
                )

                # Initialize mimetype selector pattern
                # TODO: default_mime_type returns 'text/html', regardless of
                # settings. fix in plone.app.textfield
                value_mime_type = self.value.mimeType if self.value\
                    else self.field.default_mime_type
                mt_select = etree.Element('select')
                mt_select.attrib['id'] = '{}_text_format'.format(self.id)
                mt_select.attrib['name'] = '{}.mimeType'.format(self.name)
                mt_select.attrib['class'] = mt_pattern_name
                mt_select.attrib['{}{}'.format('data-', mt_pattern_name)] =\
                    json.dumps({
                        'textareaName': self.name,
                        'widgets': {
                            'text/html': {  # TODO: currently, we only support
                                            # richtext widget config for
                                            # 'text/html', no other mimetypes.
                                'pattern': self.pattern,
                                'patternOptions': pattern_options
                            }
                        }
                    })

                # Create a list of allowed mime types
                for mt in allowed_mime_types:
                    opt = etree.Element('option')
                    opt.attrib['value'] = mt
                    if value_mime_type == mt:
                        opt.attrib['selected'] = 'selected'
                    opt.text = mt
                    mt_select.append(opt)

                # Render the combined widget
                rendered = '{}\n{}'.format(
                    textarea_widget.render(),
                    etree.tostring(mt_select)
                )
            return rendered

        if not self.value:
            return ''

        if isinstance(self.value, RichTextValue):
            return self.value.output

        return super(RichTextWidget, self).render()


# AsyncResult objects have a memory leak in them in Celery 4.2.1.
# See https://github.com/celery/celery/pull/4839/
if getattr(AsyncResult, '__del__', False):
    delattr(AsyncResult, '__del__')
