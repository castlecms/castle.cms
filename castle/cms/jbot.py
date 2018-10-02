# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import getCurrentTheme
from plone.resource.utils import queryResourceDirectory
from z3c.jbot import interfaces
from z3c.jbot.manager import find_package
from zope import interface
from zope.component import ComponentLookupError
from zope.component.hooks import getSite
from zope.filerepresentation.interfaces import IRawReadFile
from zope.globalrequest import getRequest

import Globals
import logging
import os
import sys
import traceback


REQ_CACHE_KEY = 'castle.cms.jbot.storage'

logger = logging.getLogger('castle.cms')
IGNORE = object()


_file_cache = {}


class Storage(object):

    def __init__(self):
        self.theme = getCurrentTheme()
        self.site = getSite()
        if self.theme:
            directory = queryResourceDirectory(
                THEME_RESOURCE_NAME, self.theme)
            try:
                self.themeDirectory = directory['jbot']
            except Exception:
                self.themeDirectory = None
        else:
            self.themeDirectory = None

    def __contains__(self, name):
        if self.themeDirectory:
            if name in self.themeDirectory:
                return True
        return False

    def _get_fs_path(self):
        """ returns FS path for jbot storage.
        """
        base_path = '/'.join(Globals.data_dir.split('/')[:-1])
        jbot_dir = os.path.join(base_path, 'jbot')
        site_id = self.site.getId()
        if not os.path.exists(jbot_dir):
            os.makedirs(jbot_dir)
            logger.info('created missing directory {}'.format(jbot_dir))

        fs_path = os.path.join(jbot_dir, site_id)
        if not os.path.exists(fs_path):
            os.mkdir(fs_path)
            logger.info('created missing directory {}'.format(fs_path))
        return fs_path

    def getFileFromDirectory(self, directory, filename):  # noqa
        fi = directory[filename]
        path = self._get_fs_path()
        filepath = os.path.join(path, filename)
        if fi.__class__.__name__ == "FilesystemFile":
            last_modified = fi.lastModifiedTimestamp
        else:
            last_modified = fi._p_mtime
        if not os.path.exists(filepath) or \
                DateTime(last_modified) > DateTime(os.stat(filepath).st_mtime):
            tmpfi = open(filepath, 'wb')
            if fi.__class__.__name__ == "FilesystemFile":
                data = IRawReadFile(fi).read()
            else:
                data = str(fi.data)
            tmpfi.write(data)
            tmpfi.close()
        return filepath

    def get(self, filename, template):
        # get path to file for template
        if self.themeDirectory and filename in self.themeDirectory:
            directory = self.themeDirectory
        return self.getFileFromDirectory(directory, filename)


class TemplateManager(object):
    interface.implements(interfaces.ITemplateManager)

    def __init__(self, name):
        self.name = name
        self._req = None
        self.syspaths = tuple(sys.path)

    @property
    def customized_filenames(self):
        key = '%s.%s' % (REQ_CACHE_KEY, 'customized_filenames')
        if key not in self.req.environ:
            storage = self.storage
            if storage:
                files = []
                if storage.themeDirectory:
                    files.extend(storage.themeDirectory.listDirectory())
                self.req.environ[key] = files
            else:
                self.req.environ[key] = []
        return self.req.environ[key]

    @property
    def req(self):
        if self._req is None:
            self._req = getRequest()
        return self._req

    @property
    def paths(self):
        key = '%s.%s' % (REQ_CACHE_KEY, 'paths')
        if key not in self.req.environ:
            self.req.environ[key] = {}
        return self.req.environ[key]

    @property
    def templates(self):
        key = '%s.%s' % (REQ_CACHE_KEY, 'templates')
        if key not in self.req.environ:
            self.req.environ[key] = {}
        return self.req.environ[key]

    @property
    def storage(self):
        if REQ_CACHE_KEY not in self.req.environ:
            try:
                self.req.environ[REQ_CACHE_KEY] = Storage()
            except ComponentLookupError:
                self.req.environ[REQ_CACHE_KEY] = None
        return self.req.environ[REQ_CACHE_KEY]

    def registerTemplate(self, template, token):  # noqa
        """
        wrap this method so we can log errors easily
        """
        try:
            return self._registerTemplate(template, token)
        except Exception:
            if 'jbot.error' not in self.req.environ:
                # only log one error per request
                self.req.environ['jbot.error'] = True
                logger.error(
                    'collective.jbot error: %s' % traceback.format_exc())

    def _registerTemplate(self, template, token):  # noqa
        """
        Return True if there has been a change to the override.
        Due to the nature of this implementation, a multi-site deployment
        could cause the template setting of resources to be re-set
        often. This is probably not optimal. And with chamelean I wonder if
        the compiling is re-done each time also... Eek
        """
        # assert that the template is not already registered
        filename = self.templates.get(token)
        if filename is IGNORE:
            return

        # if the template filename matches an override, we're done
        paths = self.paths
        if paths.get(filename) == template.filename and \
                os.path.exists(filename):
            return

        # verify that override has not been unregistered
        if filename is not None and filename not in paths:
            template.filename = template._filename
            del self.templates[token]

        customized = False
        if hasattr(template, '__filename'):
            # already customized by us
            path = find_package(self.syspaths, template._filename)
            customized = True
        else:
            # check if an overridable resource
            path = find_package(self.syspaths, template.filename)
            if path is None:
                # permanently ignore template
                self.templates[token] = IGNORE
                return

        filename = path.replace(os.path.sep, '.')
        # check again if filename in list of cached paths. Might be diff
        # object but same filename, we return a customized version here
        # because one request object corresponds to one site customization
        if filename in self.paths:
            if filename != template.filename:
                if not hasattr(template, '__filename'):
                    template.__filename = template.filename
                template.filename = self.paths[filename]
                return True

        if not self.storage:
            if customized:
                # revert now...
                template.filename = template.__filename
                del template.__filename
                return True
        else:
            if filename in self.customized_filenames:
                filepath = self.storage.get(filename, template)
                if filepath == template.filename:
                    # already customized with correct path, ignore
                    return

                self.paths[filename] = filepath

                # save original filename
                if not hasattr(template, '__filename'):
                    template.__filename = template.filename

                # save template, registry and assign path
                template.filename = filepath
                self.templates[token] = filename

                return True
            else:
                if customized:
                    template.filename = template.__filename
                    del template.__filename
                    return True
