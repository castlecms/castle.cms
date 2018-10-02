# -*- coding: utf-8 -*-
from zope.interface import Interface


FRAGMENTS_DIRECTORY = 'fragments'


class IFragmentsDirectory(Interface):

    def get(req, name):
        """
        """
