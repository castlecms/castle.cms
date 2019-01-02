from castle.cms.theming import renderLayout
from plone.uuid.interfaces import IUUID
from Products.Five import BrowserView
from zope.component.hooks import getSite


class AudioPlayerView(BrowserView):
    tile = 'castle.cms.audiotile'

    @property
    def params(self):
        return 'audio_files:list={uid}'.format(uid=IUUID(self.context))

    def __call__(self):
        self.request.response.setHeader('X-FRAME-OPTIONS', "ALLOWALL")
        return renderLayout(self.context, self.request, self.index(
            portal_url=getSite().absolute_url()
        ))


class VideoPlayerView(AudioPlayerView):
    tile = 'castle.cms.videotile'

    @property
    def params(self):
        return 'video:list={uid}&show_controls=1&autoplay=1'.format(
            uid=IUUID(self.context))
