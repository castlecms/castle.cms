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
                                     self.data['name'].encode('utf-8'))
        except KeyError:
            logger.error(u"Theme fragment '{0:s}' was not found.".format(
                self.data['name']
            ))
            self.index = lambda: u''

    def __call__(self):
        self.update()
        return u'<html><body>{0:s}</body></html>'.format(self.index())
