from Products.Five import BrowserView


class AudioPlayerView(BrowserView):
    def __call__(self):
        self.request.response.setHeader('X-FRAME-OPTIONS', "ALLOWALL")
        return self.index()
