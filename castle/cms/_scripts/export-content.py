from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from Acquisition import aq_parent
from Acquisition import ImplicitAcquisitionWrapper
from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from datetime import datetime
from lxml.html import fromstring
from OFS.interfaces import IFolder
from Persistence.mapping import PersistentMapping as PM1  # noqa
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping as PM2  # noqa
from plone.app.blob.field import BlobWrapper
from plone.app.blob.utils import openBlob
from Products.Archetypes import Field
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.tests.base.security import OmnipotentUser
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy
from Products.ZCatalog.Lazy import LazyCat
from StringIO import StringIO
from Testing.makerequest import makerequest
from ZODB.blob import Blob
from zope.component.hooks import setSite
from zope.dottedname.resolve import resolve
from ZPublisher.HTTPRequest import record

import argparse
import base64
import errno
import OFS
import os
import re


try:
    from Products.PressRoom.content.PressContact import PressContact
except:
    PressContact = False

try:
    from Products.CMFPlone import defaultpage
except:
    defaultpage = None

try:
    import json
except ImportError:
    import simplejson as json

try:
    from plone.app.contentlisting.contentlisting import ContentListing
except:
    ContentListing = object()


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--overwrite', dest='overwrite', default=False)
parser.add_argument('--site-id', dest='site_id', default='Plone')
parser.add_argument('--dir', dest='dir', default='./export')
args, _ = parser.parse_known_args()


def spoofRequest(app):
    """
    Make REQUEST variable to be available on the Zope application server.

    This allows acquisition to work properly
    """
    _policy = PermissiveSecurityPolicy()
    _oldpolicy = setSecurityPolicy(_policy)  # noqa
    newSecurityManager(None, OmnipotentUser().__of__(app.acl_users))
    return makerequest(app)

app = spoofRequest(app)  # noqa

user = app.acl_users.getUser('admin')  # noqa
newSecurityManager(None, user.__of__(app.acl_users))  # noqa
site = app[args.site_id]
setSite(site)

_filedata_marker = 'filedata://'
_deferred_marker = 'deferred://'
_type_marker = 'type://'
_uid_marker = 'uid://'
_uid_separator = '||||'
_date_re = re.compile('^[0-9]{4}\-[0-9]{2}\-[0-9]{2}.*$')


export_folder = os.path.abspath(args.dir)
catalog = site.portal_catalog
workflow = site.portal_workflow
ptool = site.plone_utils
site_path = '/'.join(site.getPhysicalPath())


class BaseTypeSerializer(object):
    klass = None
    toklass = None

    @classmethod
    def getTypeName(cls):
        return "%s.%s" % (cls.klass.__module__, cls.klass.__name__)

    @classmethod
    def serialize(cls, obj):
        if hasattr(obj, 'aq_base'):
            obj = obj.aq_base
        data = cls._serialize(obj)
        results = {
            'type': cls.getTypeName(),
            'data': data
        }
        return _type_marker + dumps(results)

    @classmethod
    def _serialize(cls, obj):
        return cls.toklass(obj)
    @classmethod
    def deserialize(cls, data):
        return cls._deserialize(data)
    @classmethod
    def _deserialize(cls, data):
        return cls.klass(data)


class PM1Serializer(BaseTypeSerializer):
    klass = PM1
    toklass = dict


class PM2Serializer(PM1Serializer):
    klass = PM2


class PersistentDictSerializer(BaseTypeSerializer):
    klass = PersistentDict
    toklass = dict


class OOBTreeSerializer(BaseTypeSerializer):
    klass = OOBTree
    toklass = dict


class PersistentListSerializer(BaseTypeSerializer):
    klass = PersistentList
    toklass = list


class setSerializer(BaseTypeSerializer):
    klass = set
    toklass = list


class OFSFileSerializer(BaseTypeSerializer):
    klass = OFS.Image.File
    @classmethod
    def _serialize(cls, obj):
        try:
            data = str(obj.data)
        except:
            data = str(obj.data.data)
        return {
            'data': base64.b64encode(data),
            'id': obj.id(),
            'title': obj.title,
            'content_type': obj.content_type
        }
    @classmethod
    def _deserialize(cls, data):
        file = base64.b64decode(data['data'])
        id = data['id']
        title = data['title']
        ct = data['content_type']
        return cls.klass(id, title, file, ct)


class BlobSerializer(BaseTypeSerializer):
    klass = Blob
    @classmethod
    def _serialize(cls, obj):
        blobfi = openBlob(obj)
        data = blobfi.read()
        blobfi.close()
        return {'data': base64.b64encode(data)}
    @classmethod
    def _deserialize(cls, data):
        blob = Blob()
        bfile = blob.open('w')
        data = base64.b64decode(data['data'])
        bfile.write(data)
        bfile.close()
        return blob


class OFSImageSerializer(OFSFileSerializer):
    klass = OFS.Image.Image


class DateTimeSerializer(BaseTypeSerializer):
    klass = DateTime
    @classmethod
    def getTypeName(cls):
        return 'DateTime.DateTime'
    @classmethod
    def _serialize(cls, obj):
        return obj.ISO8601()
    @classmethod
    def _deserialize(cls, data):
        return DateTime(data)


class datetimeSerializer(BaseTypeSerializer):
    klass = datetime
    @classmethod
    def _serialize(cls, obj):
        return obj.isoformat()
    @classmethod
    def _deserialize(cls, data):
        return datetime.strptime(data, '%Y-%m-%dT%H:%M:%S.%f')


class recordSerializer(BaseTypeSerializer):
    klass = record
    toklass = dict
    @classmethod
    def _deserialize(cls, data):
        rec = record()
        for key, value in data.items():
            setattr(rec, key, value)
        return rec


class ContentListingSerializer(BaseTypeSerializer):
    klass = ContentListing
    toklass = list
    @classmethod
    def _serialize(cls, obj):
        return list(obj._basesequence)
    @classmethod
    def _deserialize(cls, data):
        return LazyCat(data)


class BlobWrapperSerializer(BaseTypeSerializer):
    klass = BlobWrapper
    @classmethod
    def _serialize(cls, obj):
        blob = obj.getBlob()
        blobfi = openBlob(blob)
        data = blobfi.read()
        blobfi.close()
        return {
            'data': base64.b64encode(data),
            'filename': obj.getFilename()}
    @classmethod
    def _deserialize(cls, data):
        io = StringIO(data['data'])
        io.filename = data['filename']
        return io

_serializers = {
    PM1: PM1Serializer,
    PM2: PM2Serializer,
    PersistentDict: PersistentDictSerializer,
    OOBTree: OOBTreeSerializer,
    PersistentList: PersistentListSerializer,
    set: setSerializer,
    OFS.Image.Image: OFSImageSerializer,
    Field.Image: OFSImageSerializer,
    OFS.Image.File: OFSFileSerializer,
    DateTime: DateTimeSerializer,
    datetime: datetimeSerializer,
    record: recordSerializer,
    Blob: BlobSerializer,
    ContentListing: ContentListingSerializer,
    BlobWrapper: BlobWrapperSerializer,
}


if PressContact:
    class ContentObjectSerializer(BaseTypeSerializer):
        klass = PressContact
        @classmethod
        def _serialize(cls, obj):
            return _uid_marker + obj.UID()
        @classmethod
        def _deserialize(cls, data):
            return None
    _serializers[PressContact] = ContentObjectSerializer

class Deferred:
    pass


def customhandler(obj):
    if hasattr(obj, 'aq_base'):
        obj = obj.aq_base
    _type = type(obj)
    if _type.__name__ == 'instance':
        _type = obj.__class__
    if _type in _serializers:
        serializer = _serializers[_type]
        return serializer.serialize(obj)
    else:
        return None
    return obj


def decodeUid(v):
    v = v[len(_uid_marker):]
    return v.split(_uid_separator)


def custom_decoder(d):
    if isinstance(d, list):
        pairs = enumerate(d)
    elif isinstance(d, dict):
        pairs = d.items()
    result = []
    for k, v in pairs:
        if isinstance(v, basestring):
            if v.startswith(_filedata_marker):
                if v == _filedata_marker + _deferred_marker:
                    v = Deferred
                else:
                    filedata = v[len(_filedata_marker):]
                    if filedata:
                        v = StringIO(base64.b64decode(filedata))
                    else:
                        v = ''
            elif v.startswith(_type_marker):
                v = v[len(_type_marker):]
                results = loads(v)
                _type = resolve(results['type'])
                serializer = _serializers[_type]
                v = serializer.deserialize(results['data'])
        elif isinstance(v, (dict, list)):
            v = custom_decoder(v)
        result.append((k, v))
    if isinstance(d, list):
        return [x[1] for x in result]
    elif isinstance(d, dict):
        return dict(result)


def loads(data):
    return json.loads(data, object_hook=custom_decoder)


def dumps(data):
    return json.dumps(data, default=customhandler)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def createPath(path):
    path = path[len(site_path):]
    xpath = os.path.join(export_folder, path.lstrip('/'))
    xpathsplit = xpath.split('/')
    xfolderpath = '/'.join(xpathsplit[:-1])
    mkdir_p(xfolderpath)
    return xpath


def getReferencedImages(data):
    images = []
    for key, value in data.items():
        if not isinstance(value, basestring):
            continue
        try:
            dom = fromstring(value)
        except:
            continue
        for el in dom.cssselect('img'):
            src = el.attrib.get('src', '')
            if 'resolveuid' not in src:
                continue
            uid = src.split('resolveuid/')[-1].split(
                '/@@images')[0].split('/image_')[0]
            brains = catalog(UID=uid)
            if len(brains) > 0:
                images.append(brains[0].getObject())
    return images


def exportObj(obj):
    data = {}

    im_width = 0
    image_to_lead = None
    for field in obj.Schema().fields():
        try:
            fdata = field.getRaw(obj)
        except ValueError:
            continue
        if type(fdata) == ImplicitAcquisitionWrapper:
            fdata = fdata.aq_base
        data[field.__name__] = fdata
        if field.__name__ in ('image', 'file'):
            data[field.__name__ + '_filename'] = field.getFilename(obj)
            data[field.__name__ + '_contentType'] = field.getContentType(obj)
        if field.__name__ == 'image':
            im = field.get(obj)
            if im:
                im_width = im.width

    images = getReferencedImages(data)

    # try to find image to associate with it if there is none
    if im_width < 200:
        if len(images) > 0 and images[0].portal_type == 'Image':
            image = images[0]
            if len(image.getBackReferences(relationship='isReferencing')) < 2:
                im = image.getImage()
                data.update({
                    'image': image.Schema().getField('image').getRaw(image),
                    'image_filename': image.getFilename(),
                    'image_contentType': image.getContentType(),
                    'imageCaption': image.Description()
                })
                image_to_lead = image.UID()
                images = images[1:]

    if image_to_lead and 'text' in data:
        data['text'] = data['text'].replace(image_to_lead, obj.UID())

    is_dp = False
    if not IFolder.providedBy(obj):
        if defaultpage:
            container = aq_parent(obj)
            if container:
                is_dp = defaultpage.is_default_page(container, obj)
        else:
            is_dp = ptool.isDefaultPage(obj)

    has_sibling_pages = True
    if is_dp:
        container = aq_parent(obj)
        res = catalog(path={'query': '/'.join(container.getPhysicalPath())})
        if len([b for b in res if b.UID != image_to_lead]) > 1:
            has_sibling_pages = False

    try:
        state = workflow.getInfoFor(ob=obj, name='review_state')
    except:
        state = None
    alldata = {
        'portal_type': obj.portal_type,
        'layout': obj.getLayout(),
        'data': data,
        'uid': obj.UID(),
        'is_default_page': is_dp,
        'state': state,
        'has_sibling_pages': has_sibling_pages
    }
    yield obj, alldata
    for ref in images:
        if ref.UID() == obj.UID():
            continue
        if ref.portal_type != 'Image':
            continue
        if image_to_lead == ref.UID():
            continue
        for o, d in exportObj(ref):
            if o.UID() == ref.UID() or o.UID() == obj.UID():
                continue
            yield o, d


def writeExport(obj, data):
    objpath = '/'.join(obj.getPhysicalPath())
    if IFolder.providedBy(obj):
        objpath = os.path.join(objpath, '__folder__')
    else:
        fobj = aq_parent(obj)
        while not ISiteRoot.providedBy(fobj):
            if not os.path.exists(os.path.join('/'.join(fobj.getPhysicalPath()), '__folder__')):
                for eobj, edata in exportObj(fobj):
                    writeExport(eobj, edata)
            fobj = aq_parent(fobj)
    path = createPath(objpath)
    fi = open(path, 'w')
    fi.write(dumps(data))
    fi.close()


def runExport(brains):
    size = len(brains)
    for idx, brain in enumerate(brains):
        path = brain.getPath()
        print 'processing, ', path, ' ', str(idx + 1) + '/' + str(size)
        obj = brain.getObject()
        for obj, data in exportObj(obj):
            writeExport(obj, data)


runExport(catalog())
