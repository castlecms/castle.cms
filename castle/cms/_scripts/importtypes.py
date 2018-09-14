from castle.cms.behaviors.location import ILocation
from imghdr import what
from mimetypes import guess_type
from OFS.Image import Image
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.dexterity.behaviors.metadata import ICategorization
from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.app.event.dx.behaviors import IEventAttendees
from plone.app.event.dx.behaviors import IEventBasic
from plone.app.event.dx.behaviors import IEventContact
from plone.app.event.dx.behaviors import IEventLocation
from plone.app.textfield.value import RichTextValue
from plone.event.utils import pydt
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from StringIO import StringIO

import base64
import OFS
import re


FOLDER_DEFAULT_PAGE_LAYOUT = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
                      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"
      data-layout="./@@page-site-layout">
  <body>
    <div data-panel="content">
      <div class="mosaic-grid-row"
           data-grid='{"type": "row"}'>
        <div class="mosaic-grid-cell mosaic-width-full mosaic-position-leftmost"
             data-grid='{"type": "cell", "info":{"xs": "true", "sm": "true", "lg": "true",
                         "pos": {"x": 1, "width": 12}}}'>
          <div class="movable removable mosaic-tile mosaic-IDublinCore-title-tile">
          <div class="mosaic-tile-content">
          <div data-tile="./@@plone.app.standardtiles.field?field=IDublinCore-title"></div>
          </div>
          </div>
          <div class="movable removable mosaic-tile mosaic-IDublinCore-description-tile">
          <div class="mosaic-tile-content">
          <div data-tile="./@@plone.app.standardtiles.field?field=IDublinCore-description"></div>
          </div>
          </div>
          <div class="movable removable mosaic-tile mosaic-text-tile">
          <div class="mosaic-tile-content">
            %s
          </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
"""

_types = {}


def register_import_type(name, klass):
    _types[name] = klass


def is_base64(s):
    if hasattr(s, 'len'):
            return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,2}$', s)
    elif hasattr(s, 'size'):
            return (s.size % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,2}$', s)
    else:
            return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,2}$', s)


def decode_file_data(data):
    if isinstance(data, OFS.Image.Image):
        data = data.data
        if isinstance(data, OFS.Image.Pdata):
            return str(data)
        return data
    if isinstance(data, StringIO):
        data = data.buf
    if is_base64(data):
        return base64.b64decode(data)
    return data


def to_unicode(s):
    if not isinstance(s, unicode):
        s = s.decode('utf8')
    return s


def _generate_file_repo_object_id(path):
    path = path.lower()
    if path[0] == '/':
        path = path[1:]
    for _type in ('file', 'audio', 'video', 'videos', 'image', 'images'):
        path = path.replace('%s-repository/' % _type, '').replace('/' + _type, '')
    return path.replace('/', '-')


def DateTime_to_datetime(val):
    if hasattr(val, 'asdatetime'):
        return pydt(val)
    return val


class BaseImportType(object):
    layout = ''
    fields_mapping = {}
    data_converters = {}
    lead_image_field_names = ('image', 'leadImage', 'plone.app.contenttypes.behaviors.leadimage.ILeadImage')
    lead_image_caption_field_names = ('leadCaption', 'leadImage_caption')
    behavior_data_mappers = ()

    def __init__(self, data, path, read_phase):
        self.data = data
        self.field_data = data['data']
        self.path = path
        self.read_phase = read_phase
        self.original_type = data['portal_type']
        if data.get('is_default_page'):
            # change to be folder instead of sub-item...
            self.path = '/'.join(path.split('/')[:-1])
            self.data['portal_type'] = 'Folder'
            # disabled for now, can think about how to use this more properly...
            # if data.get('has_sibling_pages'):
            #     self.data['portal_type'] = 'Folder'

    def get_path(self):
        return self.path

    def get_data(self):
        data = {
            '_plone.uuid': self.data['uid']
        }

        try:
                id=self.field_data['id']
        except:
                try:
                        id=self.field_data['plone.app.dexterity.behaviors.id.IShortName']['id']
                except:
                        id=self.path.split('/')[-1]
        try:
                title=self.field_data['title']
        except:
                title=self.field_data['plone.app.content.interfaces.INameFromTitle']['title']
        try:
                description=self.field_data['description']
        except:
                try:
                    description=self.field_data['plone.app.dexterity.behaviors.metadata.IDublinCore']['description']
                except:
                    try:
                        description=self.field_data['plone.app.dexterity.behaviors.metadata.IBasic']['description']
                    except:
                        import pdb;pdb.set_trace()
        return dict(
            id=id,
            type=self.data['portal_type'],
            title=title,
            description=description,
            **data)

    def post_creation(self, obj):
        if obj is None:
            return
        field_data = self.field_data
        bdata = ILayoutAware(obj, None)
        if bdata:
            bdata.contentLayout = '++contentlayout++default/document.html'
        bdata = IRichText(obj, None)
        if bdata:
            try:
                    bdata.text = RichTextValue(field_data['text'], 'text/html', 'text/html')
            except:
                    try:
                        bdata.text = RichTextValue(field_data['plone.app.contenttypes.behaviors.richtext.IRichText']['text'], 'text/html', 'text/html').raw
                    except:
                        bdata.text = ''

        bdata = IBasic(obj, None)
        if bdata:
            try:
                    bdata.title = field_data['title']
            except:
                    bdata.title = field_data['plone.app.content.interfaces.INameFromTitle']['title']
            try:
                    bdata.description = field_data['description']
            except:
                    try:
                        bdata.description = field_data['plone.app.dexterity.behaviors.metadata.IDublinCore']['description']
                    except:
                        bdata.description = field_data['plone.app.dexterity.behaviors.metadata.IBasic']['description']
        else:
            obj.title = field_data['title']
            obj.description = field_data['description']

        bdata = ICategorization(obj, None)
        if bdata:
            try:
                    bdata.subjects = field_data['subject']
            except:
                    try:
                            bdata.subjects = self.field_data['plone.app.dexterity.behaviors.metadata.IDublinCore']['subjects']
                    except:
                            try:
                                bdata.subjects = self.field_data['plone.app.dexterity.behaviors.metadata.ICategorization']['subjects']
                            except:
                                pass # no keywords found

            bdata = IPublication(obj)
            try:
                    if field_data['effectiveDate']:
                        bdata.effective = pydt(field_data['effectiveDate'])
            except:
                    try:
                            if field_data['plone.app.dexterity.behaviors.metadata.IDublinCore']['effective']:
                                bdata.effective = pydt(field_data['plone.app.dexterity.behaviors.metadata.IDublinCore']['effective'])
                    except:
                            try:
                                    if field_data['plone.app.dexterity.behaviors.metadata.IPublication']['effective']:
                                        bdata.effective = pydt(field_data['plone.app.dexterity.behaviors.metadata.IPublication']['effective'])
                            except:
                                    bdata.effective = None


        ldata = ILocation(obj, None)
        if ldata:
            if field_data.get('location'):
                ldata.locations = [field_data['location']]

            if field_data.get('newsLocation'):
                if ldata.locations:
                    ldata.locations.append(field_data['newsLocation'])
                else:
                    ldata.locations = [field_data['newsLocation']]

        try:
                obj.modification_date = field_data['modification_date']
        except:
                try:
                    obj.modification_date = obj.modified()
                except:
                    obj.modification_date = None
        try:
                obj.creation_date = field_data['creation_date']
        except:
                try:
                    obj.creation_date = obj.created()
                except:
                    obj.creation_date = None

        bdata = IDublinCore(obj, None)
        if bdata:
            if 'plone.app.dexterity.behaviors.metadata.IDublinCore' in field_data.keys():
                dublin_core = field_data['plone.app.dexterity.behaviors.metadata.IDublinCore']
                bdata.expires = dublin_core['expires']
                bdata.rights = dublin_core['rights']
                bdata.creators = tuple(dublin_core['creators'])
                bdata.language = dublin_core['language']
                bdata.effective = pydt(dublin_core['effective'])
                bdata.subjects = dublin_core['subjects']
                bdata.contributors = tuple(dublin_core['contributors'])
            else:
                bdata.expires = pydt(field_data.get('expirationDate'))
                bdata.rights = field_data.get('rights')
                creators = field_data.get('creators')
                bdata.creators = tuple(creators) if creators else ()
                language = field_data.get('language')
                bdata.language = language if language is not None else ""
                bdata.effective = pydt(field_data.get('effectiveDate'))
                bdata.subjects = field_data.get('subject')
                contributors = field_data.get('contributors')
                bdata.contributors = tuple(contributors) if contributors else ()

        bdata = ILayoutAware(obj, None)
        if bdata:
            if self.data['portal_type'] == 'Folder' and 'text' in self.field_data:
                bdata.content = FOLDER_DEFAULT_PAGE_LAYOUT % self.field_data['text']
                # need to explicitly reset contentLayout value because this data
                # could be overwritten
                bdata.contentLayout = None
            elif self.layout:
                if field_data.has_key('plone.app.blocks.layoutbehavior.ILayoutAware') and field_data['plone.app.blocks.layoutbehavior.ILayoutAware'].has_key('contentLayout'):
                    bdata.contentLayout = field_data['plone.app.blocks.layoutbehavior.ILayoutAware']['contentLayout']
                if field_data.has_key('plone.app.blocks.layoutbehavior.ILayoutAware') and field_data['plone.app.blocks.layoutbehavior.ILayoutAware'].has_key('content'):
                    bdata.content = field_data['plone.app.blocks.layoutbehavior.ILayoutAware']['content']
                if self.data['data'].has_key('rendered_layout'):
                    bdata.rendered_layout = self.data['data']['rendered_layout']

        inv_field_mapping = {v: k for k, v in self.fields_mapping.iteritems()}
        for IBehavior, field_name in self.behavior_data_mappers:

            original_field_name = inv_field_mapping.get(field_name, field_name)

            if original_field_name not in self.field_data:
                # data not here...
                continue

            behavior = IBehavior(obj, None)
            if behavior is None:
                # behavior not valid for obj type
                continue

            val = self.field_data[original_field_name]

            if field_name in self.data_converters:
                val = self.data_converters[field_name](val)

            setattr(behavior, field_name, val)

        # handle lead images
        for field_name in self.lead_image_field_names:
            if self.field_data.get(field_name):
                if field_name == 'plone.app.contenttypes.behaviors.leadimage.ILeadImage':
                    im_obj = self.field_data.get(field_name)['image']
                else:
                    im_obj = self.field_data.get(field_name)
                if hasattr(im_obj, 'read'):
                    im_data = im_obj.read()
                else:
                    im_data = im_obj

                if not im_data:
                    continue

                filename = self.field_data.get('image_filename')
                if not filename:
                    if hasattr(im_obj, 'filename'):
                        filename = im_obj.filename
                    else:
                        filename = self.field_data['id']
                obj.image = im_data

                is_stringio = isinstance(im_obj, StringIO)
                if is_stringio:
                    namedblobimage_data = im_data
                else:
                    namedblobimage_data = im_data.data
                obj.image = NamedBlobImage(data=namedblobimage_data, contentType='', filename=filename)
                if not isinstance(im_obj, Image):
                    import pdb;pdb.set_trace()
                    print("    lead image is neither StringIO nor Image but unexpected type %s" % type(im_obj))

                if hasattr(obj.image, 'contentType') and isinstance(obj.image.contentType, unicode):
                    obj.image.contentType = obj.image.contentType.encode('ascii')
                else:
                    if isinstance(im_obj, Image):
                        data = im_obj.data
                    else:
                        data = im_obj.buf
                    image_type = what('', h=data)
                    if image_type in ['png', 'bmp', 'jpeg', 'xbm', 'tiff', 'gif']:
                        obj.image.contentType = 'image/%s' % image_type
                    elif image_type == 'rast':
                        obj.image.contentType = 'image/cmu-raster'
                    elif image_type == 'ppm':
                        obj.image.contentType = 'image/x-portable-pixmap'
                    elif image_type == 'pgm':
                        obj.image.contentType = 'image/x-portable-greymap'
                    elif image_type == 'pbm':
                        obj.image.contentType = 'image/x-portable-bitmap'
                    elif image_type == 'rgb':
                        obj.image.contentType = 'image/x-rgb'
                    else:
                        # look at filename extension
                        contentType, encoding = guess_type(obj.image.filename, strict=False)
                        if contentType:
                            obj.image.contentType = contentType
                        else:
                            print("    unknown image type %s encountered; defaulting to jpeg" % image_type)
                            import pdb;pdb.set_trace()
                            obj.image.contentType = 'image/jpeg' # default
                for caption_field_name in self.lead_image_caption_field_names:
                    if caption_field_name in self.field_data:
                        obj.imageCaption = self.field_data.get(caption_field_name)


class DocumentType(BaseImportType):
    layout = '++contentlayout++default/document.html'


register_import_type('Document', DocumentType)


class FolderType(BaseImportType):
    layout = '++contentlayout++castle/folder.html'


register_import_type('Folder', FolderType)


class NewsItemType(BaseImportType):

    layout = '++contentlayout++castle/news_item.html'


register_import_type('News Item', NewsItemType)


class FileType(BaseImportType):
    layout = None

    def __init__(self, data, path, read_phase):
        super(FileType, self).__init__(data, path, read_phase)
        filename = self.field_data.get('file_filename')
        if filename is None:
            filename = path.split('/')[-1]
        if filename is None:
            filename = self.field_data['title']
        try:
            _, ext = filename.lower().rsplit('.', 1)
        except:
            ext = 'pdf' # provide something so it ends up in file repository
        _id = _generate_file_repo_object_id(path)
        self.field_data['id'] = _id
        if ext in ('wav', 'mp3'):
            self.data['portal_type'] = 'Audio'
            self.path = '/audio-repository/' + _id
        elif ext in ['webm', 'ogv', 'avi', 'wmv', 'm4v',
                     'mpg', 'mpeg', 'flv', 'mp4', 'mov']:
            self.data['portal_type'] = 'Video'
            self.path = '/video-repository/' + _id
        else:
            self.path = '/file-repository/' + _id

    def get_data(self):
        data = super(FileType, self).get_data()
        filename = self.field_data.get('file_filename')
        if filename is None or not filename:
            filename = self.field_data['id']
        data['file'] = NamedBlobFile(
            data=decode_file_data(self.field_data['file']),
            filename=to_unicode(filename))
        return data


register_import_type('File', FileType)


class ImageType(BaseImportType):

    def __init__(self, data, path, read_phase):
        super(ImageType, self).__init__(data, path, read_phase)
        _id = _generate_file_repo_object_id(path)
        self.field_data['id'] = _id
        self.path = '/image-repository/' + _id


register_import_type('Image', ImageType)


class LinkType(BaseImportType):

    youtube = False

    def __init__(self, data, path, read_phase):
        super(LinkType, self).__init__(data, path, read_phase)
        url = self.field_data['remoteUrl']
        if 'youtube' in url:
            self.youtube = True
            self.data['portal_type'] = 'Video'
            _id = _generate_file_repo_object_id(path)
            self.path = '/video-repository/' + _id

    def get_path(self):
        if self.data['portal_type'] == 'Video':
            return '/video-repository/' + self.field_data['id']
        return super(LinkType, self).get_path()

    def get_data(self):
        data = super(LinkType, self).get_data()
        if self.youtube:
            data['youtube_url'] = self.field_data['remoteUrl']
        else:
            data['remoteUrl'] = self.field_data['remoteUrl']
        return data


register_import_type('Link', LinkType)


class EventType(BaseImportType):
    fields_mapping = {
        'startDate': 'start',
        'endDate': 'end',
        'eventUrl': 'event_url',
        'contactEmail': 'contact_email',
        'contactName': 'contact_name',
        'contactPhone': 'contact_phone'
    }
    data_converters = {
        'start': DateTime_to_datetime,
        'end': DateTime_to_datetime
    }
    behavior_data_mappers = (
        (IEventBasic, 'start'),
        (IEventBasic, 'end'),
        (IEventBasic, 'whole_day'),
        (IEventBasic, 'open_end'),
        (IEventAttendees, 'attendees'),
        (IEventLocation, 'location'),
        (IEventContact, 'contact_name'),
        (IEventContact, 'contact_email'),
        (IEventContact, 'contact_phone'),
        (IEventContact, 'event_url'),
    )


register_import_type('Event', EventType)


def get_import_type(data, path, read_phase):
    if data['portal_type'] in _types:
        return _types[data['portal_type']](data, path, read_phase)
    return BaseImportType(data, path, read_phase)
