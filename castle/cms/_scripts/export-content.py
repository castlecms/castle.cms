import argparse
import base64
import errno
import logging
import os
import re
from datetime import datetime
from fnmatch import fnmatch
from StringIO import StringIO

import OFS
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from Acquisition import ImplicitAcquisitionWrapper
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from lxml.html import fromstring
from OFS.interfaces import IFolder
from Persistence.mapping import PersistentMapping as PM1  # noqa
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping as PM2  # noqa
from plone.app.blob.field import BlobWrapper
from plone.app.blob.utils import openBlob
from plone.app.textfield import RichText
from Products.Archetypes import Field
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.tests.base.security import OmnipotentUser
from Products.CMFCore.tests.base.security import PermissiveSecurityPolicy
from Products.ZCatalog.Lazy import LazyCat
from Testing.makerequest import makerequest
from ZODB.blob import Blob
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import setSite
from zope.interface import Interface
from zope.schema import getFieldsInOrder
from ZPublisher.HTTPRequest import record


logger = logging.getLogger(__name__)

try:
    from plone.uuid.interfaces import IUUID
except ImportError:
    def IUUID(obj, default=None):
        return default

try:
    from Products.PressRoom.content.PressContact import PressContact
except ImportError:
    PressContact = False

try:
    from Products.CMFPlone import defaultpage
except ImportError:
    defaultpage = None

try:
    import json
except ImportError:
    import simplejson as json

try:
    from plone.app.contentlisting.contentlisting import ContentListing
except ImportError:
    ContentListing = object()

try:
    from plone.dexterity.interfaces import IDexterityContent
except ImportError:
    class IDexterityContent(Interface):
        pass

try:
    from plone.app.blocks.layoutbehavior import ILayoutAware
except ImportError:
    class ILayoutAware(Interface):
        pass


try:
    from plone.namedfile.file import NamedBlobFile
except ImportError:
    print('unable to import NamedBlobFile')
    NamedBlobFile = object()

try:
    from plone.namedfile.file import NamedFile
except ImportError:
    print('unabled to import NamedFile')
    NamedFile = object()


try:
    from plone.namedfile.file import NamedBlobImage
except ImportError:
    print('unable to import NamedBlobImage')
    NamedBlobImage = object()

try:
    from plone.app.textfield.value import RichTextValue
except ImportError:
    RichTextValue = None


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--overwrite', dest='overwrite', default=False)
parser.add_argument('--admin-user', dest='admin_user', default='admin')
parser.add_argument('--site-id', dest='site_id', default='Plone')
parser.add_argument('--dir', dest='dir', default='./export')
parser.add_argument('--modifiedsince', dest='modifiedsince')
parser.add_argument('--createdsince', dest='createdsince')
parser.add_argument(
    '--path-filter', dest='path_filter',
    default=None, required=False)
args, _ = parser.parse_known_args()


def spoof_request(app):
    """
    Make REQUEST variable to be available on the Zope application server.

    This allows acquisition to work properly
    """
    _policy = PermissiveSecurityPolicy()
    _oldpolicy = setSecurityPolicy(_policy)  # noqa
    newSecurityManager(None, OmnipotentUser().__of__(app.acl_users))
    return makerequest(app)

app = spoof_request(app)  # noqa

user = app.acl_users.getUser(args.admin_user)  # noqa
try:
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa
except Exception:
    logger.error('Unknown admin user; '
                 'specify an existing Zope admin user with --admin-user (default is admin)')  # noqa
    exit(-1)
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
    def get_type_name(cls):
        return "%s.%s" % (cls.klass.__module__, cls.klass.__name__)

    @classmethod
    def serialize(cls, obj):
        if hasattr(obj, 'aq_base'):
            obj = obj.aq_base
        data = cls._serialize(obj)
        results = {
            'type': cls.get_type_name(),
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
        except Exception:
            print('Error in OFSFileSerializer while serializing {}'.format(
                '/'.join(obj.getPhysicalPath())))
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
    def get_type_name(cls):
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
        io = StringIO(base64.b64decode(data['data']))
        io.filename = data['filename']
        return io


class NamedBlobFileSerializer(BaseTypeSerializer):
    klass = NamedBlobFile

    @classmethod
    def _serialize(cls, obj):
        return {
            'data': base64.b64encode(obj.data),
            'filename': obj.filename,
            'content_type': obj.contentType
        }

    @classmethod
    def _deserialize(cls, data):
        realdata = data['data']
        if len(realdata) < 10:  # arbitrary
            print(
                "short data found in NamedBlobFileSerializer _deserialize")
        return NamedBlobFile(
            base64.b64decode(data['data']),
            filename=data['filename'],
            contentType=data['content_type'].encode('utf-8')
        )


class NamedBlobImageSerializer(NamedBlobFileSerializer):
    klass = NamedBlobImage

    @classmethod
    def _deserialize(cls, data):
        realdata = data['data']
        if len(realdata) < 10:  # arbitrary
            print(
                "short data found in NamedBlobImageSerializer _deserialize")
        return NamedBlobImage(
            base64.b64decode(realdata),
            filename=data['filename'],
            contentType=data['content_type']
        )


class RichTextValueSerializer(BaseTypeSerializer):
    klass = RichTextValue

    @classmethod
    def _serialize(cls, obj):
        return {
            'raw': obj.raw,
            'mimeType': obj.mimeType,
            'outputMimeType': obj.outputMimeType,
            'encoding': obj.encoding
        }

    @classmethod
    def _deserialize(cls, data):
        return RichTextValue(
            raw=data['raw'],
            mimeType=data['mimeType'],
            outputMimeType=data['outputMimeType'],
            encoding=data['encoding'])


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
    NamedFile: NamedBlobFileSerializer,
    NamedBlobFile: NamedBlobFileSerializer,
    NamedBlobImage: NamedBlobImageSerializer
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


if RichTextValue is not None:
    _serializers[RichTextValue] = RichTextValueSerializer


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
        print('NOT SERIALIZING {}'.format(obj))
        return None
    return obj


def dumps(data):
    return json.dumps(data, default=custom_handler)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def get_uid(obj):
    value = IUUID(obj, None)
    if not value and hasattr(obj, 'UID'):
        value = obj.UID()
    return value


def create_path(path):
    path = path[len(site_path):]
    xpath = os.path.join(export_folder, path.lstrip('/'))
    xpathsplit = xpath.split('/')
    xfolderpath = '/'.join(xpathsplit[:-1])
    mkdir_p(xfolderpath)
    return xpath


class ContentExporter(object):

    im_width = 0
    image_to_lead = None

    def __init__(self, obj):
        self.obj = obj

    def get_field_data(self):
        pass

    def get_referenced_images(self, data):
        images = []
        for key, value in data.items():
            if not isinstance(value, basestring):
                continue
            try:
                dom = fromstring(value)
            except Exception:
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

    def get_object_data(self):
        is_dp = False
        if not IFolder.providedBy(self.obj):
            if defaultpage:
                container = aq_parent(self.obj)
                if container:
                    is_dp = defaultpage.is_default_page(container, self.obj)
            else:
                is_dp = ptool.isDefaultPage(self.obj)

        has_sibling_pages = True
        if is_dp:
            container = aq_parent(self.obj)
            res = catalog(
                path={'query': '/'.join(container.getPhysicalPath())})
            if len([b for b in res if b.UID != self.image_to_lead]) > 1:
                has_sibling_pages = False

        try:
            state = workflow.getInfoFor(ob=self.obj, name='review_state')
        except Exception:
            state = None

        try:
            review_history = workflow.getInfoFor(
                ob=self.obj, name='review_history')
        except Exception:
            review_history = []
        for h in review_history:
            h['time'] = h['time'].HTML4()

        return {
            'portal_type': self.obj.portal_type,
            'layout': self.obj.getLayout(),
            'uid': get_uid(self.obj),
            'is_default_page': is_dp,
            'state': state,
            'review_history': review_history,
            'has_sibling_pages': has_sibling_pages
        }


class ArchetypesExporter(ContentExporter):

    def get_field_data(self):
        data = {}
        if not hasattr(self.obj, 'Schema'):
            print('No schema on {}'.format(self.obj))
            return {}
        for field in self.obj.Schema().fields():
            try:
                fdata = field.getRaw(self.obj)
            except ValueError:
                continue
            if type(fdata) == ImplicitAcquisitionWrapper:
                fdata = fdata.aq_base
            data[field.__name__] = fdata
            if field.__name__ in ('image', 'file'):
                data[field.__name__ + '_filename'] = field.getFilename(
                    self.obj)
                data[field.__name__ + '_contentType'] = field.getContentType(
                    self.obj)
            if field.__name__ == 'image':
                im = field.get(self.obj)
                if im:
                    self.im_width = im.width
        return data

    def get_referenced_images(self, data):
        images = super(ArchetypesExporter, self).get_referenced_images(data)
        if self.im_width < 200:
            if len(images) > 0 and images[0].portal_type == 'Image':
                image = images[0]
                if len(image.getBackReferences(relationship='isReferencing')) < 2:  # noqa
                    data.update({
                        'image': image.Schema().getField('image').getRaw(image),  # noqa
                        'image_filename': image.getFilename(),
                        'image_contentType': image.getContentType(),
                        'imageCaption': image.Description()
                    })
                    self.image_to_lead = get_uid(image)
                    images = images[1:]
        return images


class DexterityExporter(ContentExporter):

    def get_field_data(self):
        from plone.dexterity.interfaces import IDexterityFTI
        from plone.behavior.interfaces import IBehaviorAssignable

        data = {}

        portal_type = self.obj.portal_type
        schema = getUtility(IDexterityFTI, name=portal_type).lookupSchema()
        for name, field in getFieldsInOrder(schema):
            if self.obj.portal_type == 'File' and name == 'file':
                fileobj = getattr(self.obj, name, None)
                if fileobj is not None:
                    data[name] = base64.b64encode(fileobj.data)
            else:
                data[name] = getattr(self.obj, name, None)

        behavior_assignable = IBehaviorAssignable(self.obj)
        for behavior in behavior_assignable.enumerateBehaviors():
            binst = behavior.interface(self.obj)
            bdata = {}
            for name, field in getFieldsInOrder(behavior.interface):
                if isinstance(field, RichText):
                    textfield = getattr(binst, name, None)
                    if textfield is not None:
                        bdata[name] = textfield.raw
                else:
                    bdata[name] = getattr(binst, name, None)
            data[behavior.interface.__identifier__] = bdata

        if ILayoutAware.providedBy(self.obj):
            from plone.tiles.data import ANNOTATIONS_KEY_PREFIX
            from plone.app.blocks.utils import getLayout
            from repoze.xmliter.utils import getHTMLSerializer
            from plone.app.blocks import tiles
            from plone.app.blocks import gridsystem
            from lxml.html import tostring
            tdata = {}
            annotations = IAnnotations(self.obj, {})
            for key in annotations.keys():
                if key.startswith(ANNOTATIONS_KEY_PREFIX):
                    adata = annotations[key]
                    tdata[key] = adata
            data['tile_data'] = tdata

            req = site.REQUEST
            layout = getLayout(self.obj)
            dom = getHTMLSerializer(layout)

            try:
                tiles.renderTiles(
                    req, dom.tree, site=site,
                    baseURL=self.obj.absolute_url() + '/layout_view')
            except TypeError:
                try:
                    tiles.renderTiles(
                        req, dom.tree,
                        baseURL=self.obj.absolute_url() + '/layout_view')
                except Exception:
                    tiles.renderTiles(req, dom.tree)
            gridsystem.merge(req, dom.tree)

            data['rendered_layout'] = tostring(dom.tree)

        return data


def export_archetype_obj(obj):

    exporter = ArchetypesExporter(obj)
    data = exporter.get_field_data()
    images = exporter.get_referenced_images(data)

    if exporter.image_to_lead and 'text' in data:
        data['text'] = data['text'].replace(
            exporter.image_to_lead, get_uid(obj))

    alldata = exporter.get_object_data()
    alldata['data'] = data

    yield obj, alldata
    for ref in images:
        if get_uid(ref) == get_uid(obj):
            continue
        if ref.portal_type != 'Image':
            continue
        if exporter.image_to_lead == get_uid(ref):
            continue
        for o, d in export_obj(ref):
            if get_uid(o) == get_uid(ref) or get_uid(o) == get_uid(obj):
                continue
            yield o, d


def export_dexterity_obj(obj):
    exporter = DexterityExporter(obj)
    data = exporter.get_field_data()
    alldata = exporter.get_object_data()
    alldata['data'] = data
    yield obj, alldata


def export_obj(obj):
    if IDexterityContent.providedBy(obj):
        print("--> Dexterity: %s" % obj.Title())
        func = export_dexterity_obj
    else:
        print("--> Archetypes: %s" % obj.Title())
        func = export_archetype_obj
    for result in func(obj):
        yield result


def write_export(obj, data):
    objpath = '/'.join(obj.getPhysicalPath())
    if IFolder.providedBy(obj):
        objpath = os.path.join(objpath, '__folder__')
    else:
        fobj = aq_parent(obj)
        while not ISiteRoot.providedBy(fobj):
            if not os.path.exists(
                    os.path.join('/'.join(fobj.getPhysicalPath()), '__folder__')):  # noqa
                for eobj, edata in export_obj(fobj):
                    write_export(eobj, edata)
            fobj = aq_parent(fobj)
    path = create_path(objpath)
    try:
        fi = open(path, 'w')
        fi.write(dumps(data))
        fi.close()
    except UnicodeDecodeError:
        print('Error exporting {}'.format(objpath))


def run_export(brains):
    size = len(brains)
    for idx, brain in enumerate(brains):
        path = brain.getPath()
        if (args.path_filter and
                not fnmatch(path, args.path_filter)):
            print('skipping(filtered), ', path,
                  ' ', str(idx + 1) + '/' + str(size))
            continue
        print('processing, ', path, ' ', str(idx + 1) + '/' + str(size))
        try:
            obj = brain.getObject()
        except Exception:
            print('skipping - error getting object, ', path, ' ',
                  str(idx + 1) + '/' + str(size))
            continue
        for obj, data in export_obj(obj):
            write_export(obj, data)


if args.createdsince:
    print('exporting items created since %s' % args.createdsince)
    date_range = {
        'query': (
            DateTime(args.createdsince),
            DateTime('2062-05-08 23:59:59'),
        ),
        'range': 'min:max'
    }
    query = catalog(created=date_range)
elif args.modifiedsince:
    print('exporting items modified since %s' % args.modifiedsince)
    date_range = {
        'query': (
            DateTime(args.modifiedsince),
            DateTime('2062-05-08 23:59:59'),
        ),
        'range': 'min:max'
    }
    query = catalog(modified=date_range)
else:
    query = catalog()
run_export(query)
