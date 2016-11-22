from Acquisition import aq_inner
from plone.app.contenttypes import browser
from Products.CMFCore.utils import getToolByName
from Products.MimetypesRegistry.MimeTypeItem import guess_icon_path
from zope.component import getMultiAdapter


class FileView(browser.file.FileView):

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
