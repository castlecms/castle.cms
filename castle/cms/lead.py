from castle.cms.interfaces import IReferenceNamedImage
from castle.cms.utils import has_image
from lxml.html import fromstring
from persistent.dict import PersistentDict
from persistent.mapping import PersistentMapping
from plone.app.drafts.utils import getCurrentDraft
from plone.app.uuid.utils import uuidToObject
from plone.namedfile.file import NamedBlobImage
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX
from plone.uuid.interfaces import IUUID
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides


def check_lead_image(obj, request=None):
    original_obj = obj
    if request is not None:
        # if request is passed in, we check for current draft to use...
        draft = getCurrentDraft(request)
        if draft is not None:
            obj = draft
    if has_image(obj):
        return
    image = find_image(obj)
    if image is not None:
        try:
            try:
                ct = image.image.contentType
            except AttributeError:
                ct = None
            value = NamedBlobImage(contentType=ct)
            alsoProvides(value, IReferenceNamedImage)
            value.reference = IUUID(image)
            original_obj.image = value
        except AttributeError:
            pass


def find_image_in_annotation(data):
    if type(data) in (dict, PersistentMapping, PersistentDict):
        for field_name in ('content', 'video', 'image', 'images', 'audio'):
            if field_name not in data:
                continue
            val = data[field_name]
            if not val:
                continue
            if isinstance(data, list):
                val = val[0]
            if not isinstance(val, basestring):
                continue
            val = val.strip()
            if '<' in val:
                # possible html...
                return find_image_in_html(val)
            else:
                im = uuidToObject(val)
                if im is not None and has_image(im):
                    return im


def find_image_in_html(html):
    try:
        dom = fromstring(html)
    except Exception:
        # could not parse...
        return
    for img in dom.cssselect('img'):
        src = img.attrib.get('src')
        if not src:
            continue
        if 'resolveuid' in src:
            uid = src.split('resolveuid/')[-1].split('/@@images')[0]
            ob = uuidToObject(uid)
            if ob is not None:
                return ob


def find_image(obj):
    # get data from tile data
    annotations = IAnnotations(obj, {})
    for key in annotations.keys():
        if key.startswith(ANNOTATIONS_KEY_PREFIX):
            data = annotations[key]
            im = find_image_in_annotation(data)
            if im:
                return im
    if (not getattr(obj, 'contentLayout', None) and
            getattr(obj, 'content', None)):
        im = find_image_in_html(obj.content)
        if im is not None:
            return im
    try:
        im = find_image_in_html(obj.text.raw)
        if im is not None:
            return im
    except AttributeError:
        pass
