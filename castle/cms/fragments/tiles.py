# -*- coding: utf-8 -*-
from plone.supermodel import model
from plone.tiles import Tile
from zope import schema
from zope.i18nmessageid import MessageFactory
import logging
from castle.cms.fragments.utils import getFragment

_ = MessageFactory('castle.cms')

logger = logging.getLogger('castle.cms')


class IFragmentTile(model.Schema):
    name = schema.TextLine(
        title=_(u'Name'),
    )


class FragmentTile(Tile):
    """A tile that displays a theme fragment"""

    def update(self):
        try:
            self.index = getFragment(self.context, self.request,
                                     self.data['name'])
        except KeyError:
            logger.error("Theme fragment was not found for: {}".format(
                self.data
            ))
            self.index = lambda: u''

    def __call__(self):
        self.update()
        return '<html><body>{0:s}</body></html>'.format(self.index())
