from zope.annotation.interfaces import IAnnotations

PDF_KEY = 'castle.cms.pdf'
SCREENSHOT_KEY = 'castle.cms.pdfscreenshot'


class PDFSetting(object):
    def __init__(self, obj):
        self.obj = obj
        self.annotations = IAnnotations(obj)

    def get(self, default=None):
        if self.created:
            return self.annotations[PDF_KEY]
        return default

    def put(self, blob):
        self.annotations[PDF_KEY] = blob

    def put_screenshot(self, blob):
        self.annotations[SCREENSHOT_KEY] = blob

    def get_screenshot(self, default=None):
        if self.screenshot_created:
            return self.annotations[SCREENSHOT_KEY]
        return default

    @property
    def created(self):
        return PDF_KEY in self.annotations

    @property
    def screenshot_created(self):
        return SCREENSHOT_KEY in self.annotations
