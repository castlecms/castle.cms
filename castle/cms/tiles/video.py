from castle.cms import defaults
from castle.cms.tiles.base import ContentTile
from castle.cms.widgets import VideoRelatedItemsFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import Invalid
from zope.interface import invariant
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import urlparse


class VideoTile(ContentTile):
    default_display_fields = ()

    def render(self):
        return self.index()

    def get_video(self):
        video = self.data.get('video')
        if not video:
            return
        return self.utils.get_object(self.data['video'][0])

    @property
    def show_controls(self):
        return self.data.get('show_controls', True)

    @property
    def autoplay(self):
        return self.data.get('autoplay', False)

    @property
    def loop(self):
        return self.data.get('loop', False)

    def tweak_video_url(self, url):
        # add params for properties...
        parts = url.split('/')

        # gets the 't=' start time value before cleaning the url
        parsed = urlparse.urlparse(url)
        try:
            start_time = urlparse.parse_qs(parsed.query)['t'][0]
        except KeyError:
            start_time = None

        if 'vimeo.com' in parts:
            url = 'https://player.vimeo.com/video/{id}'.format(id=parts[-1:][0])
        else:
            url = self.utils.clean_youtube_url(url)
        url += '?'
        if self.autoplay:
            url += 'autoplay=1&mute=1&'
        if not self.show_controls:
            url += 'controls=0&'
        if self.loop:
            url += 'loop=1&'
        if start_time:
            url += 'start=%s' % start_time[:-1]
        return url


class IVideoTileSchema(model.Schema):

    form.widget(video=VideoRelatedItemsFieldWidget)
    video = schema.List(
        title=u"Video file",
        description=u"Reference video file on the site.",
        required=False,
        default=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    youtube_url = schema.TextLine(
        title=u'YouTube url',
        description=u'Or provide a YouTube or Vimeo url',
        required=False)

    @invariant
    def validate_video(data):
        if data.video and len(data.video) != 1:
            raise Invalid("Must select 1 video")
        if data.video and data.youtube_url:
            raise Invalid("You can not select both a video and a youtube url")
        if not data.video and not data.youtube_url:
            raise Invalid("Must select a video or a youtube url")
        if data.video:
            utils = getMultiAdapter((getSite(), getRequest()),
                                    name="castle-utils")
            obj = utils.get_object(data.video[0])
            if obj.portal_type != 'Video':
                raise Invalid('Must provide video file')

    form.widget('display_fields', CheckBoxFieldWidget)
    display_fields = schema.Tuple(
        title=u'Display fields',
        description=u'Fields that should show from the content',
        default=(),
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleTerm('title', 'title', u'Title'),
                SimpleTerm('description', 'description', u'Overview/Summary'),
                SimpleTerm('date', 'date', u'Date'),
                SimpleTerm('transcript', 'transcript', u'Transcript'),
            ])
        )
    )

    display_type = schema.Choice(
        title=u'Display type',
        required=True,
        default=defaults.get('video_tile_displaytype', u'landscape'),
        vocabulary=SimpleVocabulary([
            SimpleTerm('landscape', 'landscape', u'Landscape'),
            SimpleTerm('square', 'square', u'Square'),
            SimpleTerm('fullwidth', 'fullwidth', u'Full width'),
        ])
    )

    show_controls = schema.Bool(
        title=u'Show controls',
        default=True
    )

    autoplay = schema.Bool(
        title=u'Autoplay',
        default=defaults.get('video_tile_autoplay', False, 'bool')
    )

    loop = schema.Bool(
        title=u'Loop',
        default=defaults.get('video_tile_loop', False, 'bool')
    )
