from castle.cms.files import aws
from castle.cms.interfaces import IReferenceNamedImage
from cStringIO import StringIO
from os import fstat
from PIL import Image
from plone import api
from plone.app.blob.download import handleRequestRange
from plone.app.blob.iterators import BlobStreamIterator
from plone.app.blob.utils import openBlob
from plone.app.imaging.utils import getAllowedSizes
from plone.namedfile import browser as namedfile
from plone.namedfile.interfaces import INamedBlobFile
from plone.namedfile.scaling import ImageScaling
from Products.Five import BrowserView
from webdav.common import rfc1123_date
from zExceptions import NotFound

import base64
import zope.publisher.interfaces


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
            return self.serve_file()

        url = aws.get_url(self.context)
        self.request.response.redirect(url)


class DownloadBlob(BrowserView):

    content_type = 'application/pdf'
    file_ext = 'pdf'

    def get_data(self):
        raise NotImplemented()

    def __call__(self):
        data = self.get_data()
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
