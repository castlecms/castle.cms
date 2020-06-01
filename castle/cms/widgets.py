import json
import os
from base64 import b64decode

import z3c.form.browser.textarea
import z3c.form.interfaces
import z3c.form.widget
from Acquisition import aq_parent
from castle.cms import utils
from castle.cms.behaviors.leadimage import IRequiredLeadImage
from castle.cms.interfaces import ICastleLayer
from castle.cms.interfaces import IReCaptchaWidget
from castle.cms.interfaces import IReferenceNamedImage
from castle.cms.tiles.views import getTileViews
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.uuid.utils import uuidToObject
from plone.app.widgets.base import InputWidget as BaseInputWidget
from plone.app.widgets.base import TextareaWidget as BaseTextareaWidget
from plone.app.z3cform.widget import AjaxSelectWidget as pz3c_AjaxSelectWidget
from plone.app.z3cform.widget import BaseWidget
from plone.app.z3cform.widget import QueryStringWidget as BaseQueryStringWidget
from plone.app.z3cform.widget import RelatedItemsWidget as BaseRelatedItemsWidget  # noqa
from plone.app.z3cform.widget import SelectWidget as pz3c_SelectWidget
from plone.formwidget.namedfile.converter import NamedDataConverter
from plone.formwidget.namedfile.interfaces import INamedFileWidget
from plone.formwidget.namedfile.interfaces import INamedImageWidget
from plone.formwidget.namedfile.widget import NamedFileWidget
from plone.formwidget.namedfile.widget import NamedImageWidget as BaseNamedImageWidget  # noqa
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from plone.namedfile.interfaces import INamedFileField
from plone.namedfile.interfaces import INamedImageField
from plone.namedfile.utils import safe_basename
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFPlone import utils as ploneutils
from z3c.form.browser import text
from z3c.form.browser.checkbox import SingleCheckBoxWidget
from z3c.form.browser.select import SelectWidget as z3cform_SelectWidget
from z3c.form.interfaces import NOVALUE
from z3c.form.interfaces import IFieldWidget
from z3c.form.interfaces import ITextWidget
from z3c.form.util import getSpecification
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.component import adapts
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import implements
from zope.interface import implementsOnly
from zope.schema.interfaces import IField
from zope.schema.interfaces import IList
from ZPublisher.HTTPRequest import FileUpload
from castle.cms.vocabularies import ReallyUserFriendlyTypesVocabulary as FriendlyTypesVocab


class MultiSelectWidget(pz3c_SelectWidget):
    multiple = True


class QueryStringWidget(BaseQueryStringWidget):
    """
    okay, maybe this sucks, I'm not sure.
    but we're sort of customizing how the widget works with our tiles here...
    """

    def _base_args(self):
        args = super(QueryStringWidget, self)._base_args()
        args['pattern_options']['showPreviews'] = False
        return args


class RelatedItemsWidget(BaseRelatedItemsWidget):
    initialPath = None
    base_criteria = []

    def _base_args(self):
        args = super(RelatedItemsWidget, self)._base_args()
        args['pattern_options']['width'] = ''
        args['pattern_options']['initialPath'] = self.initialPath
        base_criteria = self.base_criteria[:]
        args['pattern_options']['baseCriteria'] = base_criteria
        return args


class RelatedItemWidget(RelatedItemsWidget):

    def _base_args(self):
        args = super(RelatedItemWidget, self)._base_args()
        args['pattern_options']['maximumSelectionSize'] = 1
        return args


class ImageRelatedItemsWidget(RelatedItemsWidget):

    initialPath = '/image-repository'

    def _base_args(self):
        args = super(ImageRelatedItemsWidget, self)._base_args()
        args['pattern_options']['selectableTypes'] = ['Image']
        args['pattern_options']['baseCriteria'].append({
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Image', 'Folder']
        })
        return args


class ImageRelatedItemWidget(RelatedItemsWidget):

    initialPath = '/image-repository'

    def _base_args(self):
        args = super(ImageRelatedItemWidget, self)._base_args()
        args['pattern_options']['maximumSelectionSize'] = 1
        args['pattern_options']['selectableTypes'] = ['Image']
        args['pattern_options']['baseCriteria'].append({
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Image', 'Folder']
        })
        return args


class FileRelatedItemsWidget(RelatedItemsWidget):

    initialPath = '/file-repository'

    def _base_args(self):
        args = super(FileRelatedItemsWidget, self)._base_args()
        args['pattern_options']['selectableTypes'] = ['File', 'Audio', 'Video']
        args['pattern_options']['baseCriteria'] = [{
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['File', 'Audio', 'Video', 'Folder']
        }]
        return args


class VideoRelatedItemsWidget(RelatedItemsWidget):

    initialPath = '/video-repository'

    def _base_args(self):
        args = super(VideoRelatedItemsWidget, self)._base_args()
        args['pattern_options']['selectableTypes'] = ['Video']
        args['pattern_options']['baseCriteria'] = [{
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Video', 'Folder']
        }]
        return args


class AudioRelatedItemsWidget(RelatedItemsWidget):

    initialPath = '/audio-repository'

    def _base_args(self):
        args = super(AudioRelatedItemsWidget, self)._base_args()
        args['pattern_options']['selectableTypes'] = ['Audio']
        args['pattern_options']['baseCriteria'] = [{
            'i': 'portal_type',
            'o': 'plone.app.querystring.operation.selection.any',
            'v': ['Audio', 'Folder']
        }]
        return args


class SlideRelatedItemsWidget(RelatedItemsWidget):

    def get_friendly_types_without_folder(self):
        friendly_portal_types_vocab = FriendlyTypesVocab()(self.context)
        friendly_portal_types = friendly_portal_types_vocab.by_value.keys()
        friendly_portal_types.remove('Folder')
        return friendly_portal_types

    def _base_args(self):
        args = super(SlideRelatedItemsWidget, self)._base_args()

        args['pattern_options']['selectableTypes'] = self.get_friendly_types_without_folder()
        args['pattern_options']['baseCriteria'] = [
            {
                'i': 'self_or_child_has_title_description_and_image',
                'o': 'plone.app.querystring.operation.boolean.isTrue'
            },
        ]
        args['pattern_options']['allowAdd'] = False
        args['pattern_options']['folderTypes'] = ['Folder']
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def QueryFieldWidget(field, request):
    return z3c.form.widget.FieldWidget(field, QueryStringWidget(request))


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def RelatedItemsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, RelatedItemsWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def RelatedItemFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, RelatedItemWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def ImageRelatedItemsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         ImageRelatedItemsWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def ImageRelatedItemFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         ImageRelatedItemWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def FileRelatedItemsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         FileRelatedItemsWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def SlideRelatedItemsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, SlideRelatedItemsWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def VideoRelatedItemsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         VideoRelatedItemsWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def AudioRelatedItemsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         AudioRelatedItemsWidget(request))
    widget.vocabulary = 'plone.app.vocabularies.Catalog'
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def SelectFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         pz3c_SelectWidget(request))
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def MultiSelectFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         MultiSelectWidget(request))
    return widget


class IJSONListWidget(ITextWidget):
    """Marker interface for the Select2Widget."""


class JsonListWidget(BaseWidget):
    """Ajax select widget for z3c.form."""

    _base = BaseInputWidget

    implementsOnly(IJSONListWidget)

    pattern = 'mapselect'
    pattern_options = BaseWidget.pattern_options.copy()

    def _base_args(self):
        args = super(JsonListWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = (self.request.get(self.name,
                                          self.value) or u'[]').strip()
        return args


class IMapMarkersWidget(IJSONListWidget):
    """Marker interface for the Select2Widget."""


class MapMarkersWidget(JsonListWidget):
    implementsOnly(IMapMarkersWidget)

    pattern = 'mapselect'
    pattern_options = JsonListWidget.pattern_options.copy()

    def _base_args(self):
        args = super(MapMarkersWidget, self)._base_args()
        args.setdefault('pattern_options')
        args['pattern_options']['type'] = 'markers'
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def MapMarkersFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, MapMarkersWidget(request))
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def UseQueryWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, SingleCheckBoxWidget(request))
    widget.addClass('pat-castledynamicform')
    return widget


class MapPointWidget(BaseWidget):
    """Ajax select widget for z3c.form."""

    _base = BaseInputWidget

    implementsOnly(IMapMarkersWidget)

    klass = style = title = lang = onclick = ondblclick = onmousedown = ''
    onmouseup = onmouseover = onmousemove = onmouseout = onkeypress = ''
    onkeydown = onkeyup = ''

    pattern = 'mapselect'
    pattern_options = BaseWidget.pattern_options.copy()

    def _base_args(self):
        args = super(MapPointWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = (self.request.get(self.name,
                                          self.value) or u'{}').strip()

        args.setdefault('pattern_options', {})
        args['pattern_options']['type'] = 'point'
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def MapPointFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, MapPointWidget(request))
    return widget


class MapPointsWidget(MapPointWidget):
    """Ajax select widget for z3c.form."""

    _base = BaseInputWidget

    implementsOnly(IMapMarkersWidget)

    pattern = 'mapselect'
    pattern_options = BaseWidget.pattern_options.copy()

    def _base_args(self):
        args = super(MapPointsWidget, self)._base_args()
        args['value'] = (self.request.get(self.name,
                                          self.value) or u'[]').strip()
        args['pattern_options']['type'] = 'points'
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def MapPointsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, MapPointsWidget(request))
    return widget


class IFileUploadFieldsWidget(IJSONListWidget):
    """Marker interface for the Select2Widget."""


class FileUploadFieldsWidget(MapPointsWidget):
    implementsOnly(IFileUploadFieldsWidget)
    pattern = 'fileuploadfieldswidget'

    def _base_args(self):
        args = super(FileUploadFieldsWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = (self.request.get(self.name,
                                          self.value) or u'[]').strip()
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def FileUploadFieldsFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field,
                                         FileUploadFieldsWidget(request))
    return widget


class JSONListWidgetDataConverter(NamedDataConverter):
    """Converts from a file-upload to a NamedFile variant.
    """
    adapts(IList, IJSONListWidget)

    def toWidgetValue(self, value):
        return json.dumps(value)

    def toFieldValue(self, value):
        fields = json.loads(value)
        for field in fields or []:
            if 'required' in field and isinstance(field['required'], bool):
                field['required'] = unicode(field['required']).lower()
        return fields


class PreviewSelectWidget(pz3c_SelectWidget):

    previews = {}
    tile_name = None
    pattern = 'previewselect'

    def _base_args(self):
        args = super(PreviewSelectWidget, self)._base_args()
        args.setdefault('pattern_options', {
        })
        previews = self.previews.copy()
        if self.tile_name:
            for view in getTileViews(aq_parent(self.context),
                                     self.request, self.tile_name):
                previews[view.name] = view.preview
        args['pattern_options']['previews'] = previews
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def PreviewSelectFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, PreviewSelectWidget(request))
    return widget


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def NavigationTypeWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, z3cform_SelectWidget(request))
    widget.addClass('pat-castledynamicform')
    return widget


class ReCaptchaWidget(text.TextWidget):
    maxlength = 7
    size = 8

    implementsOnly(IReCaptchaWidget)

    def public_key(self):
        registry = getUtility(IRegistry)
        return registry.get('castle.recaptcha_public_key', '')


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def ReCaptchaFieldWidget(field, request):
    """IFieldWidget factory for CaptchaWidget."""
    return z3c.form.widget.FieldWidget(field, ReCaptchaWidget(request))


class ITinyMCETextWidget(ITextWidget):
    """Marker interface for the Select2Widget."""


class TinyMCETextWidget(BaseWidget):
    """Ajax select widget for z3c.form."""

    _base = BaseTextareaWidget

    implementsOnly(ITinyMCETextWidget)

    pattern = 'tinymce'
    pattern_options = BaseWidget.pattern_options.copy()

    def _base_args(self):
        args = super(TinyMCETextWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = self.request.get(self.name, self.value) or ''
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def TinyMCETextFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, TinyMCETextWidget(request))
    return widget


class AjaxSelectWidget(pz3c_AjaxSelectWidget):

    def _base_args(self):
        args = super(AjaxSelectWidget, self)._base_args()
        vurl = args['pattern_options']['vocabularyUrl']
        if vurl.count('@@') == 2:
            # badly generated url
            split = vurl.split('@@')
            args['pattern_options']['vocabularyUrl'] = '%s/@@%s' % (
                split[0], split[-1])
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def AjaxSelectFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, AjaxSelectWidget(request))
    return widget


class IFocalNamedImageWidget(INamedImageWidget):
    pass


class FocalNamedImageWidget(BaseNamedImageWidget):
    """A widget for a named file object
    """
    implements(IFocalNamedImageWidget)

    def get_image_options(self):
        download_url = self.download_url
        contentType = getattr(self.value, 'contentType', None)
        if contentType and 'gif' in contentType:
            contentType = 'image/png'
            download_url = '%s/@@download-as-png' % self.context.absolute_url()

        width = height = 0
        focal_point = [0, 0]
        try:
            width, height = self.value.getImageSize()
            try:
                focal_point = self.value.focal_point
            except Exception:
                focal_point = self.context._image_focal_point
        except Exception:
            if self.value:
                try:
                    focal_point = [width / 2, height / 2]
                except Exception:
                    pass
        try:
            fct = self.file_content_type
        except Exception:
            fct = None
        try:
            icon = self.file_icon
        except Exception:
            icon = None
        return {
            'exists': self.value is not None,
            'download_url': download_url,
            'filename': self.filename,
            'content_type': contentType,
            'icon': icon,
            'thumb_width': self.thumb_width,
            'file_size': self.file_size,
            'doc_type': fct,
            'width': width,
            'height': height,
            'focal_point': focal_point
        }

    def get_reference_options(self):
        download_url = self.download_url
        if (isinstance(self.value, basestring) and
                self.value.startswith('reference:')):
            reference = self.value.replace('reference:', '')
        else:
            reference = self.value.reference
        return {
            'reference': reference,
            'exists': False,
            'download_url': download_url,
            'filename': self.filename
        }

    @property
    def pattern_options(self):
        result = {
            'reference': None,
            'id': self.id,
            'title': self.title,
            'required': self.required,
            'allow_nochange': self.allow_nochange,
            'name': self.name,
            'disabled': self.disabled,
            'maxlength': self.maxlength
        }
        is_string = isinstance(self.value, basestring)
        if (IReferenceNamedImage.providedBy(self.value) or
                (is_string and self.value.startswith('reference:'))):
            result.update(self.get_reference_options())
        else:
            result.update(self.get_image_options())
        return json.dumps(result)


@adapter(getSpecification(ILeadImage['image']), ICastleLayer)
@implementer(IFieldWidget)
def LeadImageFocalNamedImageFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, FocalNamedImageWidget(request))
    return widget


@adapter(getSpecification(IRequiredLeadImage['image']), ICastleLayer)
@implementer(IFieldWidget)
def RequiredLeadImageFocalNamedImageFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, FocalNamedImageWidget(request))
    return widget


@adapter(INamedImageField, ICastleLayer)
@implementer(IFieldWidget)
def FocalNamedImageFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, FocalNamedImageWidget(request))
    return widget


class FocalNamedImageDataConverter(NamedDataConverter):
    """Converts from a file-upload to a NamedFile variant.
    """
    adapts(INamedImageField, IFocalNamedImageWidget)

    def toWidgetValue(self, value):
        return value

    def getImage(self, value):
        widget = self.widget
        req = widget.request

        if isinstance(value, FileUpload):

            filename = safe_basename(value.filename)

            if filename is not None and not isinstance(filename, unicode):
                # Work-around for
                # https://bugs.launchpad.net/zope2/+bug/499696
                filename = filename.decode('utf-8')

            value.seek(0)
            data = value.read()
            if data or filename:
                value = self.field._type(data=data, filename=filename)
            else:
                return self.get_missing_image()

        else:
            args = {}
            if req.get(widget.name + '.filename'):
                filename = req.get(widget.name + '.filename')
                if type(filename) in (list, set, tuple) and filename:
                    filename = filename[0]
                if not isinstance(filename, unicode):
                    filename = filename.decode('utf8')
                args['filename'] = filename
            if isinstance(value, basestring):
                if value.startswith('reference:'):
                    reference = value.replace('reference:', '')
                    obj = uuidToObject(reference)
                    if obj:
                        try:
                            try:
                                ct = obj.image.contentType
                            except AttributeError:
                                ct = None
                            value = NamedBlobImage(contentType=ct)
                            alsoProvides(value, IReferenceNamedImage)
                            value.reference = reference
                        except AttributeError:
                            pass
                elif value.startswith('data:'):
                    value = b64decode(value.split(',')[-1])
                    value = self.field._type(data=value, **args)
            else:
                try:
                    value = self.field._type(data=str(value), **args)
                except UnicodeEncodeError:
                    value = self.field._type(data=value.encode('utf8'), **args)

        return value

    def get_missing_image(self):
        if hasattr(self.widget.context, self.field.__name__):
            return getattr(self.widget.context, self.field.__name__)
        return self.field.missing_value

    def toFieldValue(self, value):
        widget = self.widget
        req = widget.request
        action = req.get(widget.name + '.action')

        if action == 'remove':
            return self.field.missing_value

        if value is None or value == '':
            return self.get_missing_image()

        if action not in ('nochange',):
            value = self.getImage(value)

        if not value:
            # another attempt to safe guard
            return self.get_missing_image()

        if not IReferenceNamedImage.providedBy(value):
            # set focal point data
            try:
                fp = [
                    float(req.form.get(widget.name + '.focalX')),
                    float(req.form.get(widget.name + '.focalY'))
                ]
                value.focal_point = fp
                # backup in case other doesn't save
                self.widget.context._image_focal_point = fp
            except Exception:
                pass
        return value


class IFocalPointSelectWidget(ITextWidget):
    """Marker interface for the Select2Widget."""


class FocalPointSelectWidget(BaseWidget):
    """Widget to select focal point"""

    _base = BaseInputWidget

    implementsOnly(IFocalPointSelectWidget)

    pattern = 'focalpointselect'
    pattern_options = BaseWidget.pattern_options.copy()

    def _base_args(self):
        args = super(FocalPointSelectWidget, self)._base_args()
        args['name'] = self.name
        args['value'] = (self.request.get(self.name,
                                          self.value) or u'').strip()
        return args


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def FocalPointSelectFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(
        field, FocalPointSelectWidget(request))
    return widget


class ITOCWidget(IJSONListWidget):
    """Marker interface for the Select2Widget."""


class TOCWidget(JsonListWidget):
    implementsOnly(IMapMarkersWidget)

    pattern = 'toccreator'
    pattern_options = JsonListWidget.pattern_options.copy()


@adapter(IField, ICastleLayer)
@implementer(IFieldWidget)
def TOCFieldWidget(field, request):
    widget = z3c.form.widget.FieldWidget(field, TOCWidget(request))
    return widget


class TmpFile(object):

    def __init__(self, info):
        self.info = info


class IUploadNamedFileWidget(INamedFileWidget):
    pass


class NamedFileDataConverter(NamedDataConverter):
    """Converts from a file-upload to a NamedFile variant.
    """
    adapts(INamedFileField, IUploadNamedFileWidget)

    def toWidgetValue(self, value):
        return value

    def toFieldValue(self, value):
        extracted = self.widget.extract()
        if isinstance(extracted, TmpFile):
            info = extracted.info
            if not os.path.exists(info['tmp_file']):
                return
            fi = open(info['tmp_file'], 'r')
            filename = ploneutils.safe_unicode(info['name'])
            annotations = IAnnotations(self.widget.context)
            tmp_files = annotations['_tmp_files']
            val = NamedBlobFile(data=fi, filename=filename)
            del tmp_files[info['field_name']]
            return val
        return super(NamedFileDataConverter, self).toFieldValue(value)


@implementer(IUploadNamedFileWidget)
class UploadNamedFileWidget(NamedFileWidget):
    klass = NamedFileWidget.klass + ' pat-upload-update'
    replacement = False

    @property
    def pattern_options(self):
        return json.dumps({
            'field_name': self.name,
            'tmp_field_id': self.get_tmp_field_id(),
            'uid': IUUID(self.context, None)
        })

    @property
    def cache_name(self):
        return '__cache_' + self.name

    def get_tmp_field_id(self):
        action = self.request.get("%s.action" % self.name, None)
        try:
            action = json.loads(action)
            if action.get('replace'):
                return action['tmp_field_id']
        except (ValueError, TypeError):
            pass
        return 'tmp_' + utils.get_random_string()

    def extract(self, default=NOVALUE):
        if getattr(self.request, self.cache_name, None):
            return getattr(self.request, self.cache_name)

        action = self.request.get("%s.action" % self.name, None)
        try:
            action = json.loads(action)
            if action.get('replace'):
                self.replacement = True
                annotations = IAnnotations(self.context)
                if '_tmp_files' not in annotations:
                    return default
                tmp_files = annotations['_tmp_files']
                if action['tmp_field_id'] not in tmp_files:
                    return default
                info = tmp_files[action['tmp_field_id']]
                val = TmpFile(info)
                setattr(self.request, self.cache_name, val)
                return val
            else:
                return super(UploadNamedFileWidget, self).extract(default)
        except (ValueError, TypeError):
            return super(UploadNamedFileWidget, self).extract(default)


@implementer(IFieldWidget)
@adapter(INamedFileField, ICastleLayer)
def NamedFileFieldWidget(field, request):
    # unfortunately we can't customize ONLY for that particular
    # type of field since the video|audio|file is done with xml schema :(
    if field.__name__ == 'file':
        return z3c.form.widget.FieldWidget(field, UploadNamedFileWidget(request))
    else:
        return z3c.form.widget.FieldWidget(field, NamedFileWidget(request))
