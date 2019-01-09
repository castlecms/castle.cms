import base64
import logging
from cStringIO import StringIO
from os import fstat

import zope.publisher.interfaces
from Acquisition import aq_inner
from castle.cms.files import aws
from castle.cms.interfaces import IReferenceNamedImage
from PIL import Image
from plone import api
from plone.app.blob.download import handleRequestRange
from plone.app.blob.iterators import BlobStreamIterator
from plone.app.blob.utils import openBlob
from plone.app.contenttypes.browser import file
from plone.app.imaging.utils import getAllowedSizes
from plone.namedfile import browser as namedfile
from plone.namedfile.interfaces import INamedBlobFile
from plone.namedfile.scaling import ImageScaling
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.MimetypesRegistry.MimeTypeItem import guess_icon_path
from webdav.common import rfc1123_date
from zExceptions import NotFound
from ZODB.POSException import POSKeyError
from zope.component import getMultiAdapter


logger = logging.getLogger('castle.cms')


class DownloadAsPNG(BrowserView):
    base64 = False

    def get_data(self):
        if not self.context.image:
            raise NotFound

        blob = self.context.image._blob
        return openBlob(blob)

    def __call__(self):
        fi = self.get_data()
        im = Image.open(fi)

        changed = StringIO()
        im.save(changed, 'PNG')
        changed.seek(0)
        if hasattr(fi, 'close'):
            fi.close()
        data = changed.read()

        if self.base64:
            data = base64.b64encode(data)

        resp = self.request.response
        resp.setHeader('Content-Disposition',
                       'inline; filename=%s.png' % self.context.getId())
        resp.setHeader("Content-Length", data)
        resp.setHeader('Content-Type', 'image/png')
        return data


class ConvertToPNG(DownloadAsPNG):
    base64 = True

    def get_data(self):
        return self.request.form['data']


class Download(namedfile.Download):

    def serve_file(self):
        file = self._getFile()
        self.set_headers(file)
        if not INamedBlobFile.providedBy(file):
            return super(Download, self).__call__()

        request_range = handleRequestRange(
            self.context, file.getSize(), self.request, self.request.response)
        return BlobStreamIterator(file._blob, **request_range)

    def __call__(self):
        if not aws.uploaded(self.context):
            try:
                return self.serve_file()
            except (POSKeyError, SystemError):
                # if there is no blob file, just give out 404
                raise NotFound

        url = aws.get_url(self.context)
        self.request.response.redirect(url)


class DownloadBlob(BrowserView):

    content_type = 'application/pdf'
    file_ext = 'pdf'

    def get_data(self):
        raise NotImplementedError()

    def __call__(self):
        try:
            data = self.get_data()
        except IOError:
            # can be from zeo client blob file weirdness with PIL
            # ocassionally
            logger.info('Could not get blob data', exc_info=True)
            raise NotFound

        if data:
            is_blob = False
            if isinstance(data, basestring):
                length = len(data)
            else:
                is_blob = True
                blobfi = openBlob(data)
                length = fstat(blobfi.fileno()).st_size
                blobfi.close()

            self.request.response.setHeader(
                'Last-Modified',
                rfc1123_date(self.context._p_mtime))
            resp = self.request.response
            resp.setHeader('Content-Disposition',
                           'inline; filename=%s.%s' % (self.context.getId(), self.file_ext))
            resp.setHeader("Content-Length", length)
            resp.setHeader('Content-Type', self.content_type)

            if is_blob:
                resp.setHeader('Accept-Ranges', 'bytes')
                range = handleRequestRange(
                    self.context, length, self.request,
                    self.request.response)
                return BlobStreamIterator(data, **range)
            else:
                return data
        else:
            raise NotFound


class EmptyRedirect(BrowserView):
    '''
    I just want to redirect.
    Yes, this doc string is required because Zope2 is insane
    '''

    __roles__ = ('Anonymous',)

    def __init__(self, *args):
        super(EmptyRedirect, self).__init__(*args)
        self.sizes = getAllowedSizes()

    def __call__(self):
        return self

    def __getattr__(self, name):
        if name in self.sizes:
            return self
        raise AttributeError


class CastleImageScaling(ImageScaling):

    def publishTraverse(self, request, name):
        if name == 'image':
            if IReferenceNamedImage.providedBy(self.context.image):
                # auth not setup yet, we just redirect and assume we'll figure the rest out
                catalog = api.portal.get_tool('portal_catalog')
                brains = catalog.unrestrictedSearchResults(UID=self.context.image.reference)
                if len(brains) > 0:
                    brain = brains[0]
                    url = request.ACTUAL_URL.replace(
                        self.context.absolute_url(), brain.getURL())
                    request.response.redirect(url)
                    view = EmptyRedirect(self.context, self.request)
                    return view.__of__(self.context)
        return super(CastleImageScaling, self).publishTraverse(request, name)


class NamedFileDownload(Download):
    def __call__(self):
        try:
            return super(NamedFileDownload, self).__call__()
        except AttributeError:
            raise zope.publisher.interfaces.NotFound(self, self.fieldname, self.request)


class FileView(file.FileView):

    @property
    def moved(self):
        return getattr(self.context.file, 'original_filename', None) is not None

    @property
    def filename(self):
        fi = self.context.file
        return getattr(fi, 'original_filename', fi.filename)

    @property
    def size(self):
        fi = self.context.file
        return getattr(fi, 'original_size', fi.getSize())

    @property
    def content_type(self):
        fi = self.context.file
        return getattr(fi, 'original_content_type', fi.contentType)

    def get_mimetype_icon(self):
        context = aq_inner(self.context)
        pstate = getMultiAdapter(
            (context, self.request),
            name=u'plone_portal_state'
        )
        portal_url = pstate.portal_url()
        mtr = getToolByName(context, "mimetypes_registry")
        mime = []
        if self.content_type:
            mime.append(mtr.lookup(self.content_type))
        if self.filename:
            mime.append(mtr.lookupExtension(self.filename))
        mime.append(mtr.lookup("application/octet-stream")[0])
        icon_paths = [m.icon_path for m in mime if hasattr(m, 'icon_path')]
        if icon_paths:
            return portal_url + "/" + icon_paths[0]

        return portal_url + "/" + guess_icon_path(mime[0])
