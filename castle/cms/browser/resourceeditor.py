from plone.resourceeditor.browser import FileManager
from plone.resourceeditor.browser import FileManagerActions


class CastleCMSResourceEditorErrorResponse(FileManagerActions):
    def saveFile(self, path, value):
        return super(CastleCmsResourceEditorErrorResponse, self).saveFile(path, value)
    
