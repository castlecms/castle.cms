from castle.cms.interfaces import IReferenceNamedImage
from AccessControl import Unauthorized
from Acquisition import aq_base
from Acquisition import aq_parent
from castle.cms.behaviors.location import ILocation
from castle.cms.interfaces import IHasDefaultImage
from castle.cms.interfaces import ITrashed
from plone import api
from plone.app.contenttypes.interfaces import IFile
from plone.app.contenttypes.interfaces import IImage
from plone.dexterity.interfaces import IDexterityContent
from plone.indexer.decorator import indexer
from plone.uuid.interfaces import IUUID
from ZODB.POSException import POSKeyError


@indexer(IDexterityContent)
def getRawRelatedItems(obj):
    try:
        result = []
        for relation in obj.relatedItems:
            try:
                to_obj = relation.to_object
                if to_obj:
                    uuid = IUUID(to_obj)
                    if uuid:
                        result.append(uuid)
            except AttributeError:
                pass
        return result
    except AttributeError:
        return []


@indexer(ILocation)
def getLocation(obj):
    bdata = ILocation(obj, None)
    if bdata and bdata.location:
        return bdata.location[0]


@indexer(IDexterityContent)
def hasImage(obj):
    if IHasDefaultImage.providedBy(obj):
        return True
    return getattr(aq_base(obj), 'image', None) is not None


@indexer(IDexterityContent)
def image_info(obj):
    try:
        image = obj.image
        if IReferenceNamedImage.providedBy(image):
            data = {'reference': image.reference}
        else:
            width, height = image.getImageSize()
            data = {
                'width': width,
                'height': height,
                'focal_point': [width / 2, height / 2]
            }

            try:
                data['focal_point'] = image.focal_point
            except AttributeError:
                try:
                    data['focal_point'] = obj._image_focal_point
                except:
                    pass
        return data
    except AttributeError:
        pass


@indexer(IDexterityContent)
def getContentTypeContent(obj):
    return 'text/html'


@indexer(IFile)
def getContentTypeFile(obj):
    try:
        return obj.file.original_content_type
    except:
        try:
            return obj.file.contentType
        except:
            pass


@indexer(IImage)
def getContentTypeImage(obj):
    try:
        return obj.image.contentType
    except:
        pass


@indexer(IDexterityContent)
def trashed(obj):
    while obj:
        if ITrashed.providedBy(obj):
            return True
        obj = aq_parent(obj)
    return False


@indexer(IDexterityContent)
def last_modified_by(context):
    try:
        creator = api.user.get_current().getId()
    except:
        try:
            creator = context.Creators()[0]
        except:
            creator = 'admin'

    rt = api.portal.get_tool("portal_repository")

    if rt is None or not rt.isVersionable(context):
        # not versionable; fallback to the creator
        return creator

    try:
        history = rt.getHistoryMetadata(context)
    except Unauthorized:
        history = None
    if not history:
        return creator

    try:
        if not rt.isUpToDate(context):
            return creator
    except POSKeyError:
        return creator

    length = history.getLength(countPurged=False)

    last = history.retrieve(length - 1)
    if not last or type(last) != dict:
        # unexpected version metadata; fallback to the creator
        return creator

    metadata = last.get("metadata")
    if not metadata or type(metadata) != dict:
        # unexpected version metadata; fallback to the creator
        return creator

    sys_metadata = metadata.get("sys_metadata")
    if not sys_metadata or type(sys_metadata) != dict:
        # unexpected version metadata; fallback to the creator
        return creator

    principal = sys_metadata.get("principal")
    if not principal or type(principal) != str:
        # unexpected version metadata; fallback to the creator
        return creator

    return principal
