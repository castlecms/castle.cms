import json

from castle.cms.tiles.base import BaseImagesTile
from castle.cms.widgets import ImageRelatedItemsFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary


class SliderTile(BaseImagesTile):

    @property
    def pattern_options(self):
        opts = {
            'animation': self.data.get('animation', 'fade'),
            'controlNav': self.data.get('controlNav', True),
            'directionNav': self.data.get('directionNav', True),
            'slideshowSpeed': self.data.get('slideshowSpeed', 7000),
            'animationSpeed': self.data.get('animationSpeed', 600)
        }
        return json.dumps(opts)

    def render(self):
        return self.index()

    @property
    def height(self):
        return self.data.get('height', 250)


class ISliderTileSchema(model.Schema):

    form.widget(images=ImageRelatedItemsFieldWidget)
    images = schema.List(
        title=u"Images",
        description=u"Select images or folders of images to display in slider."
                    u" If the image has a related item selected, that "
                    u"related item will be used for the link and description "
                    u"for the slide display",
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Catalog'
        )
    )

    animation = schema.Choice(
        title=u'Animation',
        vocabulary=SimpleVocabulary([
            SimpleVocabulary.createTerm('fade', 'fade', 'Fade'),
            SimpleVocabulary.createTerm('slide', 'slide', 'Slide'),
        ]),
        default='fade'
    )

    controlNav = schema.Bool(
        title=u'Control nav',
        default=True)

    directionNav = schema.Bool(
        title=u'Direction nav',
        default=True)

    slideshowSpeed = schema.Int(
        title=u'Cycle speed',
        description=u'In milliseconds',
        default=7000)

    animationSpeed = schema.Int(
        title=u'Animation speed',
        description=u'In milliseconds',
        default=600)
