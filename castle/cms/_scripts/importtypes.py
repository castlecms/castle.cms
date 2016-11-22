import base64
import re

from castle.cms.behaviors.location import ILocation
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.dexterity.behaviors.metadata import ICategorization
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.app.textfield.value import RichTextValue
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage


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


def isBase64(s):
    return (len(s) % 4 == 0) and re.match('^[A-Za-z0-9+/]+[=]{0,2}$', s)


def decodeFileData(data):
    if isinstance(data, OFS.Image.Image):
        data = data.data
        if isinstance(data, OFS.Image.Pdata):
            return str(data)
        return data
    if isBase64(data):
        return base64.b64decode(data)
    return data


def toUnicode(s):
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


class BaseImportType(object):
    layout = ''

    def __init__(self, data, path, read_phase):
        self.data = data
        self.field_data = data['data']
        self.path = path
        self.read_phase = read_phase
        self.original_type = data['portal_type']
        if data.get('is_default_page'):
            self.path = '/'.join(path.split('/')[:-1])
            if data.get('has_sibling_pages'):
                self.data['portal_type'] = 'Folder'

    def get_path(self):
        return self.path

    def get_data(self):
        data = {
            '_plone.uuid': self.data['uid']
        }
        if self.field_data.get('image'):
            im_data = self.field_data.get('image')
            if hasattr(im_data, 'read'):
                im_data = im_data.read()
            filename = self.field_data.get('image_filename')
            if not filename:
                filename = self.field_data['id']
            data['image'] = NamedBlobImage(
                data=decodeFileData(im_data),
                filename=toUnicode(filename))
            if not data['image'].contentType:
                data['image'].contentType = 'image/jpeg'
            data['imageCaption'] = self.field_data.get('imageCaption')
        return dict(
            id=self.field_data['id'],
            type=self.data['portal_type'],
            title=self.field_data['title'],
            description=self.field_data['description'],
            **data)

    def post_creation(self, obj):
        field_data = self.field_data
        bdata = ILayoutAware(obj, None)
        if bdata:
            bdata.contentLayout = '++contentlayout++default/document.html'
        bdata = IRichText(obj, None)
        if bdata:
            bdata.text = RichTextValue(field_data['text'], 'text/html', 'text/html')

        bdata = IBasic(obj, None)
        if bdata:
            bdata.title = field_data['title']
            bdata.description = field_data['description']
        else:
            obj.title = field_data['title']
            obj.description = field_data['description']

        bdata = ICategorization(obj, None)
        if bdata:
            bdata.subjects = field_data['subject']

            bdata = IPublication(obj)
            if field_data['effectiveDate']:
                bdata.effective = field_data['effectiveDate'].asdatetime()

        ldata = ILocation(obj, None)
        if ldata:
            if field_data.get('location'):
                ldata.locations = [field_data['location']]

            if field_data.get('newsLocation'):
                if ldata.locations:
                    ldata.locations.append(field_data['newsLocation'])
                else:
                    ldata.locations = [field_data['newsLocation']]

        obj.modification_date = field_data['modification_date']
        obj.creation_date = field_data['creation_date']

        bdata = ILayoutAware(obj, None)
        if bdata:
            if self.data['portal_type'] == 'Folder' and 'text' in self.field_data:
                bdata.content = FOLDER_DEFAULT_PAGE_LAYOUT % self.field_data['text']
            elif self.layout:
                bdata.contentLayout = self.layout


class DocumentType(BaseImportType):
    layout = '++contentlayout++default/document.html'
_types['Document'] = DocumentType

class FolderType(BaseImportType):
    layout = '++contentlayout++castle/folder.html'
_types['Folder'] = FolderType


class NewsItemType(BaseImportType):

    layout = '++contentlayout++castle/newsitem.html'

_types['News Item'] = NewsItemType


class FileType(BaseImportType):
    layout = None

    def __init__(self, data, path, read_phase):
        super(FileType, self).__init__(data, path, read_phase)
        filename = self.field_data.get('file_filename')
        _, ext = filename.lower().rsplit('.', 1)
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
        data['file'] = NamedBlobFile(
            data=decodeFileData(self.field_data['file'].read()),
            filename=toUnicode(self.field_data.get('file_filename')))
        return data
_types['File'] = FileType


class ImageType(BaseImportType):

    def __init__(self, data, path, read_phase):
        super(ImageType, self).__init__(data, path, read_phase)
        _id = _generate_file_repo_object_id(path)
        self.field_data['id'] = _id
        self.path = '/image-repository/' + _id
_types['Image'] = ImageType


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
_types['Link'] = LinkType


def getImportType(data, path, read_phase):
    if data['portal_type'] in _types:
        return _types[data['portal_type']](data, path, read_phase)
    return BaseImportType(data, path, read_phase)
