from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from datetime import datetime
from Persistence.mapping import PersistentMapping as PM1
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping as PM2
from plone.app.blob.field import BlobWrapper
from plone.app.blob.utils import openBlob
from plone.app.contentlisting.contentlisting import ContentListing
from plone.namedfile.file import NamedBlobImage
from Products.ZCatalog.Lazy import LazyCat
from StringIO import StringIO
from ZODB.blob import Blob
from zope.dottedname.resolve import resolve
from ZPublisher.HTTPRequest import record

import base64
import json
import OFS
import re


_filedata_marker = 'filedata://'
_deferred_marker = 'deferred://'
_type_marker = 'type://'
_uid_marker = 'uid://'
_uid_separator = '||||'
_date_re = re.compile('^[0-9]{4}\-[0-9]{2}\-[0-9]{2}.*$')


class BaseTypeSerializer(object):
    klass = None
    toklass = None

    @classmethod
    def get_type_name(kls):
        return "%s.%s" % (kls.klass.__module__, kls.klass.__name__)

    @classmethod
    def serialize(kls, obj):
        if hasattr(obj, 'aq_base'):
            obj = obj.aq_base
        data = kls._serialize(obj)
        results = {
            'type': kls.get_type_name(),
            'data': data
        }
        return _type_marker + dumps(results)

    @classmethod
    def _serialize(kls, obj):
        return kls.toklass(obj)

    @classmethod
    def deserialize(kls, data):
        return kls._deserialize(data)

    @classmethod
    def _deserialize(kls, data):
        return kls.klass(data)


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
    def _serialize(kls, obj):
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
    def _deserialize(kls, data):
        file = base64.b64decode(data['data'])
        id = data['id']
        title = data['title']
        ct = data['content_type']
        return kls.klass(id, title, file, ct)


class BlobSerializer(BaseTypeSerializer):
    klass = Blob

    @classmethod
    def _serialize(kls, obj):
        blobfi = openBlob(obj)
        data = blobfi.read()
        blobfi.close()
        return {'data': base64.b64encode(data)}

    @classmethod
    def _deserialize(kls, data):
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
    def get_type_name(kls):
        return 'DateTime.DateTime'

    @classmethod
    def _serialize(kls, obj):
        return obj.ISO8601()

    @classmethod
    def _deserialize(kls, data):
        return DateTime(data)


class datetimeSerializer(BaseTypeSerializer):
    klass = datetime

    @classmethod
    def _serialize(kls, obj):
        return obj.isoformat()

    @classmethod
    def _deserialize(kls, data):
	try:
		return datetime.strptime(data, '%Y-%m-%dT%H:%M:%S.%f')
	except:
		return datetime.strptime(data, '%Y-%m-%dT%H:%M:%S')


class recordSerializer(BaseTypeSerializer):
    klass = record
    toklass = dict

    @classmethod
    def _deserialize(kls, data):
        rec = record()
        for key, value in data.items():
            setattr(rec, key, value)
        return rec


class ContentListingSerializer(BaseTypeSerializer):
    klass = ContentListing
    toklass = list

    @classmethod
    def _serialize(kls, obj):
        return list(obj._basesequence)

    @classmethod
    def _deserialize(kls, data):
        return LazyCat(data)


class BlobWrapperSerializer(BaseTypeSerializer):
    klass = BlobWrapper

    @classmethod
    def _serialize(kls, obj):
        blob = obj.getBlob()
        blobfi = openBlob(blob)
        data = blobfi.read()
        blobfi.close()
        return {
            'data': base64.b64encode(data),
            'filename': obj.getFilename()}

    @classmethod
    def _deserialize(kls, data):
        io = StringIO(base64.b64decode(data['data']))
        io.filename = data['filename']
        return io


class NamedBlobImageSerializer(BaseTypeSerializer):
    klass = NamedBlobImage

    @classmethod
    def _serialize(cls, obj):
        return {
            'data': base64.b64encode(obj.data),
            'filename': obj.filename,
            'content_type': obj.contentType
        }

    @classmethod
    def _deserialize(cls, data):
        return NamedBlobImage(
            base64.b64decode(data['data']),
            filename=data['filename'],
            contentType=data['content_type']
        )


_serializers = {
    PM1: PM1Serializer,
    PM2: PM2Serializer,
    PersistentDict: PersistentDictSerializer,
    OOBTree: OOBTreeSerializer,
    PersistentList: PersistentListSerializer,
    set: setSerializer,
    OFS.Image.Image: OFSImageSerializer,
    OFS.Image.File: OFSFileSerializer,
    DateTime: DateTimeSerializer,
    datetime: datetimeSerializer,
    record: recordSerializer,
    Blob: BlobSerializer,
    ContentListing: ContentListingSerializer,
    BlobWrapper: BlobWrapperSerializer,
    NamedBlobImage: NamedBlobImageSerializer
}


class Deferred:
    pass


def custom_handler(obj):
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
                try:
                    _type = resolve(results['type'])
                    serializer = _serializers[_type]
                    v = serializer.deserialize(results['data'])
                except ImportError:
                    pass
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
    return json.dumps(data, default=custom_handler)
