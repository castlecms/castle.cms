# -*- coding: utf-8 -*-
import os.path

from castle.cms.fragments import FragmentsDirectory
from castle.cms.fragments.interfaces import IFragmentsDirectory

from zope.interface import Interface
from zope.component import getGlobalSiteManager
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.fields import PythonIdentifier
from zope.schema import TextLine


class IFragmentDirectoryDirective(Interface):

    directory = TextLine(
        title=u'Directory path',
        description=u'Path relative to the package.',
        required=True
        )

    name = PythonIdentifier(
        title=u'Name',
        description=u'Name of the directory. If not specified, the name of '
                    u'the current package is used.',
        required=True,
        )


def registerFragmentDirectory(_context, directory, name=None, type=None):

    """

    Register a zcml fragment folder declaration

    This is shamelessly adapted from the zope plone folder declaration
    at https://github.com/plone/plone.resource/blob/master/plone/resource/zcml.py

    """  # noqa
    if _context.package and os.path.isabs(directory):
        raise ConfigurationError('Resource directories in distributions must '
                                 'be specified as relative paths.')
    elif _context.package:
        directory = _context.path(directory)
    elif not _context.package and not os.path.isabs(directory):
        raise ConfigurationError('Global resource directories must be '
                                 'specified as absolute paths.')

    if '..' in directory.split('/'):
        raise ConfigurationError('Traversing to parent directories '
                                 'via .. is not allowed.')
    if not os.path.exists(directory):
        raise IOError('Directory not found: %s' % directory)

    if name is None and _context.package:
        name = _context.package.__name__

    fd = FragmentsDirectory()
    fd.directory_path = directory

    gsm = getGlobalSiteManager()
    gsm.registerUtility(fd, IFragmentsDirectory, name)
