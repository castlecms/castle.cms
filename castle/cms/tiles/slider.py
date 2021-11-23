from castle.cms.tiles.base import BaseImagesTile
from castle.cms.tiles.content import IImagesTileSchema
from zope import schema
from plone.supermodel import model
from zope.schema.vocabulary import SimpleVocabulary

import json


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


DEFAULT_SLIDER_CONFIGURATION = {
    'animation': 'fade',
    'controlNav': True,
    'directionNav': True,
    'slideshowSpeed': 7000,
    'animationSpeed': 600,
}


class ISliderTileConfiguration(model.Schema):
    animation = schema.Choice(
        title=u'Animation',
        vocabulary=SimpleVocabulary([
            SimpleVocabulary.createTerm('fade', 'fade', 'Fade'),
            SimpleVocabulary.createTerm('slide', 'slide', 'Slide'),
        ]),
        default=DEFAULT_SLIDER_CONFIGURATION['animation'],
    )

    controlNav = schema.Bool(
        title=u'Control nav',
        default=DEFAULT_SLIDER_CONFIGURATION['controlNav'],
    )

    directionNav = schema.Bool(
        title=u'Direction nav',
        default=DEFAULT_SLIDER_CONFIGURATION['directionNav'],
    )

    slideshowSpeed = schema.Int(
        title=u'Cycle speed',
        description=u'In milliseconds',
        default=DEFAULT_SLIDER_CONFIGURATION['slideshowSpeed'],
    )

    animationSpeed = schema.Int(
        title=u'Animation speed',
        description=u'In milliseconds',
        default=DEFAULT_SLIDER_CONFIGURATION['animationSpeed'],
    )


class ISliderTileSchema(IImagesTileSchema, ISliderTileConfiguration):
    pass
