from collections import Mapping
import logging

from Acquisition import aq_base
from z3c.form import interfaces
from z3c.form.validator import SimpleFieldValidator
from zope.component import getMultiAdapter
from zope.interface import Invalid
from zope.schema.interfaces import IBytes
from zope.security.proxy import removeSecurityProxy



logger = logging.getLogger('castle.cms')

BACKEND_URL_ERROR = u'This content contains a backend URL ({}) and cannot be saved.'
_CONTENT_SAVE_FORMS = None


def _unwrap(obj):
    if obj is None:
        return None
    return aq_base(removeSecurityProxy(obj))


def _as_text(value):
    if isinstance(value, unicode):
        return value
    if isinstance(value, str):
        return unicode(value, 'utf-8', 'replace')
    return None


def _content_save_forms():
    global _CONTENT_SAVE_FORMS
    if _CONTENT_SAVE_FORMS is None:
        from plone.app.tiles.browser.add import DefaultAddForm as TileAddForm
        from plone.app.tiles.browser.edit import DefaultEditForm as TileEditForm
        from plone.dexterity.browser.add import DefaultAddForm
        from plone.dexterity.browser.edit import DefaultEditForm
        _CONTENT_SAVE_FORMS = (
            DefaultEditForm,
            DefaultAddForm,
            TileEditForm,
            TileAddForm,
        )
    return _CONTENT_SAVE_FORMS


def is_content_save_form(view):
    """True for content add/edit and tile edit forms, including fieldset groups."""
    seen = set()
    current = view
    forms = _content_save_forms()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        current = _unwrap(current)
        if isinstance(current, forms):
            return True
        current = getattr(current, 'parentForm', None)
    return False


def iter_text_values(value):
    """Yield unicode strings stored in a submitted field value."""
    if value is None or value is interfaces.NOT_CHANGED or value is interfaces.NO_VALUE:
        return
    text = _as_text(value)
    if text is not None:
        if text:
            yield text
        return
    raw = getattr(value, 'raw', None)
    if raw is not None and hasattr(value, 'mimeType'):
        text = _as_text(raw)
        if text:
            yield text
        return
    if isinstance(value, Mapping):
        for item in value.values():
            for text in iter_text_values(item):
                yield text
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            for text in iter_text_values(item):
                yield text


def find_backend_urls(value, utils):
    needles = []
    for url in utils.invalid_backend_urls:
        url = _as_text(url)
        if url:
            folded = url.lower()
            if folded not in needles:
                needles.append(folded)
    found = []
    for text in iter_text_values(value):
        haystack = text.lower()
        for url in needles:
            if url in haystack and url not in found:
                found.append(url)
    return found


def _backend_url_utils(request):
    utils = getattr(request, '_castle_backend_url_utils', None)
    if utils is None:
        from castle.cms.browser.content import BackendUrlUtils
        utils = BackendUrlUtils()
        try:
            request._castle_backend_url_utils = utils
        except Exception:
            logger.debug('Could not cache backend URL utils on the request', exc_info=True)
    return utils


def _stored_value(context, field):
    if context is None or field is None:
        return None
    try:
        manager = getMultiAdapter((context, field), interfaces.IDataManager)
        return manager.query()
    except Exception:
        logger.debug('Could not read stored value for backend URL check', exc_info=True)
        return None


class BackendUrlValidator(SimpleFieldValidator):
    """Reject content saves that include a configured backend URL."""

    def validate(self, value, force=False):
        if is_content_save_form(self.view) and not IBytes.providedBy(self.field):
            self._reject_backend_urls(value)
        return super(BackendUrlValidator, self).validate(value, force)

    def _reject_backend_urls(self, value):
        if value is interfaces.NOT_CHANGED or value is interfaces.NO_VALUE:
            value = _stored_value(self.context, self.field)
        found = find_backend_urls(value, _backend_url_utils(self.request))
        if found:
            raise Invalid(BACKEND_URL_ERROR.format(u', '.join(found)))


def _iter_widgets(form, seen=None):
    if seen is None:
        seen = set()
    if form is None or id(form) in seen:
        return
    seen.add(id(form))
    widgets = getattr(form, 'widgets', None)
    if widgets is not None:
        for widget in widgets.values():
            yield widget
    for group in getattr(form, 'groups', ()) or ():
        for widget in _iter_widgets(group, seen):
            yield widget
    parent = getattr(_unwrap(form), 'parentForm', None)
    for widget in _iter_widgets(parent, seen):
        yield widget


def promote_backend_url_status(form):
    """Replace the generic form error with the backend URL message.

    Mosaic keeps the layout field hidden, so a widget error there is easy to miss.
    """
    if getattr(form, 'status', None) != getattr(form, 'formErrorsMessage', None):
        return
    for widget in _iter_widgets(form):
        error = getattr(widget, 'error', None)
        message = getattr(error, 'message', None)
        text = _as_text(message)
        if text is None and message is not None:
            try:
                text = unicode(message)
            except Exception:
                text = None
        if text and u'backend URL' in text:
            form.status = message
            return


def button_handler_call(self, form, action):
    result = self._old___call__(form, action)
    try:
        promote_backend_url_status(form)
    except Exception:
        logger.warning('Could not show backend URL save error', exc_info=True)
    return result
