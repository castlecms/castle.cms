from Products.Five import BrowserView
from castle.cms.theming import renderWithTheme
from plone.uuid.interfaces import IUUID

IFRAME_MINIMAL_LAYOUT = """<!doctype html>
<html class="no-js" lang="en-us" data-gridsystem="bs3">
  <head>
    <meta charset="utf-8" />

    <link data-tile="${{portal_url}}/@@plone.app.standardtiles.stylesheets"/>
    <meta name="generator" content="Castle - https://www.wildcardcorp.com"/>
    <style>
    body {{
        padding: 0;
        margin: 0;
    }}
    </style>
  </head>
  <body id="visual-portal-wrapper">
    <div class="castle-container">
    <div class="row main-content main-content col-count-1">
    <div id="main-content" class="col-md-12">
        <div class="mosaic-grid-row row">
            <div class="mosaic-grid-cell mosaic-width-full mosaic-position-leftmost col-md-12">
                <div data-tile="./@@{tile}?{params}"></div>
            </div>
        </div>
    </div>
    </div>
    </div>

    <link data-tile="${{portal_url}}/@@plone.app.standardtiles.javascripts"/>
  </body>
</html>
"""


class AudioPlayerView(BrowserView):
    def __call__(self):
        self.request.response.setHeader('X-FRAME-OPTIONS', "ALLOWALL")
        self.request.environ['X-CASTLE-LAYOUT'] = IFRAME_MINIMAL_LAYOUT.format(
            tile='castle.cms.audiotile',
            params='audio_files:list={uid}'.format(uid=IUUID(self.context))
        )
        return renderWithTheme(
            self.context, self.request, '<div />')


class VideoPlayerView(AudioPlayerView):
    def __call__(self):
        self.request.response.setHeader('X-FRAME-OPTIONS', "ALLOWALL")
        self.request.environ['X-CASTLE-LAYOUT'] = IFRAME_MINIMAL_LAYOUT.format(
            tile='castle.cms.videotile',
            params='video:list={uid}&show_controls=1&autoplay=1'.format(uid=IUUID(self.context))
        )
        return renderWithTheme(
            self.context, self.request, '<div />')
