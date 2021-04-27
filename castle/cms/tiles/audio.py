from castle.cms.tiles.base import ContentTile
from castle.cms.widgets import AudioRelatedItemsFieldWidget
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
from castle.cms.widgets import PreviewSelectFieldWidget


class AudioTile(ContentTile):
    default_display_fields = ()
    default_player_type = 'simple'

    def render(self):
        return self.index()

    @property
    def audios(self):
        res = []
        audios = self.data.get('audio_files', [])
        if audios:
            for obj in audios:
                obj = self.utils.get_object(obj)
                try:
                    obj.file
                except AttributeError:
                    continue
                res.append(obj)
        return res

    @property
    def player_type(self):
        pt = self.data.get('player_type', None)
        if not pt:
            pt = self.default_player_type
        return pt

    @property
    def author_name(self):
        an = self.data.get('author_name', None)
        if not an:
            an = ""
        return an

    def get_url(self, audio):
        fi = audio.file
        return '%s/@@download/file/%s' % (audio.absolute_url(), fi.filename)

    def get_content_type(self, audio):
        fi = audio.file
        return fi.contentType


class IAudioTileSchema(model.Schema):

    form.widget(audio_files=AudioRelatedItemsFieldWidget)
    audio_files = schema.List(
        title=u"Audio files",
        description=u"Reference a files on the site. You can provide more "
                    u"than one audio file in the case you'd like to provide "
                    u"additional audio formats that'll play on different "
                    u"browsers and phones.",
        required=False,
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    @invariant
    def validate_audio_files(data):
        utils = getMultiAdapter((getSite(), getRequest()),
                                name="castle-utils")
        if data.audio_files:
            for audio in data.audio_files:
                obj = utils.get_object(audio)
                if obj.portal_type != 'Audio':
                    raise Invalid('Must provide only audio files')
        else:
            raise Invalid('Must provide audio file(s)')

    width = schema.TextLine(
        title=u"Width",
        default=u'100%',
        required=False
    )

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

    form.widget('player_type', PreviewSelectFieldWidget,
                previews={
                    'simple': '++plone++castle/images/previews/audioplayers/simple.png',
                    'advanced': '++plone++castle/images/previews/audioplayers/advanced.png',
                    'advancedthumbnail': '++plone++castle/images/previews/audioplayers/thumbnail.png',
                    'advancedbackground': '++plone++castle/images/previews/audioplayers/background.png'
                })

    player_type = schema.Choice(
        title=u'Player Type',
        description=u'Choose an audio player',
        default=u'simple',
        required=False,
        vocabulary=SimpleVocabulary([
            SimpleTerm('simple', 'simple', u'Simple'),
            SimpleTerm('advanced', 'advanced', u'Advanced'),
            SimpleTerm('advancedthumbnail', 'advancedthumbnail', u'Advanced with thumbnail'),
            SimpleTerm('advancedbackground', 'advancedbackground', u'Advanced with background image')
        ])
    )

    author_name = schema.TextLine(
        title=u"Author Name",
        default=u"",
        required=False)
