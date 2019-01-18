from castle.cms.interfaces import IUploadedToYoutube
from plone.dexterity.browser import edit
from plone.z3cform import layout
from z3c.form.interfaces import HIDDEN_MODE
from castle.cms.services.google import youtube


class VideoEditForm(edit.DefaultEditForm):
    def update(self):
        super(VideoEditForm, self).update()
        if IUploadedToYoutube.providedBy(self.context):
            # can only move these to youtube...
            self.widgets['upload_to_youtube'].mode = HIDDEN_MODE
            self.widgets['youtube_url'].mode = HIDDEN_MODE
        elif youtube.get_oauth_token() is None:
            self.widgets['upload_to_youtube'].mode = HIDDEN_MODE


VideoEditView = layout.wrap_form(VideoEditForm)
