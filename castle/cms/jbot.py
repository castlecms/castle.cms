# -*- coding: utf-8 -*-
import logging
import os
import sys
import time
import traceback

import Globals
from DateTime import DateTime
from plone import api
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import getCurrentTheme
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory
from z3c.jbot import interfaces
from z3c.jbot.manager import find_package
from zope import interface
from zope.component import ComponentLookupError
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.filerepresentation.interfaces import IRawReadFile
from zope.globalrequest import getRequest
from zope.interface import providedBy


REQ_CACHE_KEY = 'castle.cms.jbot.storage'

logger = logging.getLogger('castle.cms')
IGNORE = object()


class Storage(object):

    def __init__(self):
        self.theme = getCurrentTheme()
        self.site = getSite()
        if self.theme:
            directory = queryResourceDirectory(
                THEME_RESOURCE_NAME, self.theme)
            try:
                self.jbot_directory = directory['jbot']
            except Exception:
                self.jbot_directory = None
        else:
            self.jbot_directory = None

    def __contains__(self, name):
        if self.jbot_directory is not None:
            if name in self.jbot_directory:
                return True
        return False

    def _get_fs_path(self):
        """ returns FS path for jbot storage.
        """
        base_path = '/'.join(Globals.data_dir.split('/')[:-1])
        jbot_dir = os.path.join(base_path, 'jbot')
        site_id = '-'.join(self.site.getPhysicalPath()[1:])
        fs_path = os.path.join(jbot_dir, site_id, self.theme)
        if not os.path.exists(fs_path):
            os.makedirs(fs_path)
            logger.info('created missing directory {}'.format(fs_path))
        return fs_path

    def get_filepath(self, filename):
        modified = self.get_modified(filename)
        path = self._get_fs_path()
        return os.path.join(path, '{}-{}'.format(
            int(modified), filename))

    def get_customizations(self):
        files = {}
        if self.jbot_directory is not None:
            for filename in self.jbot_directory.listDirectory():
                filepath = self.get_filepath(filename)
                if self.file_modified(filename, filepath):
                    self.write_customization(filename)
                files[filename] = {
                    'modified': self.get_modified(filename),
                    'filepath': filepath
                }
        return files

    def write_customization(self, filename):
        fi = self.jbot_directory[filename]
        filepath = self.get_filepath(filename)
        with open(filepath, 'wb') as tmpfi:
            if fi.__class__.__name__ == "FilesystemFile":
                data = IRawReadFile(fi).read()
            else:
                data = str(fi.data)
            tmpfi.write(data)
        return filepath

    def get_modified(self, filename):
        fi = self.jbot_directory[filename]
        if fi.__class__.__name__ == "FilesystemFile":
            return fi.lastModifiedTimestamp
        else:
            return fi._p_mtime

    def file_modified(self, filename, filepath):
        return (not os.path.exists(filepath) or
                DateTime(self.get_modified(filename)) > DateTime(os.stat(filepath).st_mtime))


class _TemplateManager(object):
    interface.implements(interfaces.ITemplateManager)

    def __init__(self):
        self.syspaths = tuple(sys.path)
        self.templates = {}
        self.cache = {}

    def get_storage(self):
        try:
            return Storage()
        except ComponentLookupError:
            return None

    def _get_customizations(self):
        storage = self.get_storage()
        if storage is None:
            return {}
        else:
            return storage.get_customizations()

    def get_customizations(self):
        req = getRequest()
        key = '{}.customizations'.format(REQ_CACHE_KEY)
        if key not in req.environ:
            if api.env.debug_mode():
                req.environ[key] = self._get_customizations()
            else:
                # check for value in cache
                cache_key = providedBy(req)  # layer is cache key
                if cache_key not in self.cache:
                    self.cache[cache_key] = {
                        'when': time.time(),
                        'value': self._get_customizations()
                    }
                else:
                    registry = queryUtility(IRegistry)
                    theme_cache_time = getattr(registry, '_theme_cache_mtime', 0)
                    if theme_cache_time > self.cache[cache_key]['when']:
                        self.cache[cache_key] = {
                            'when': time.time(),
                            'value': self._get_customizations()
                        }
                req.environ[key] = self.cache[cache_key]['value']
        return req.environ[key]

    def registerTemplate(self, template, token):  # noqa
        """
        wrap this method so we can log errors easily
        """
        try:
            return self._registerTemplate(template, token)
        except Exception:
            req = getRequest()
            if 'jbot.error' not in req.environ:
                # only log one error per request
                req.environ['jbot.error'] = True
                logger.error(
                    'collective.jbot error: {}'.format(traceback.format_exc()))

    def _registerTemplate(self, template, original):  # noqa
        """
        Return True if there has been a change to the override.
        """
        # check if template is ignored, no filename to override
        filename = self.templates.get(template)
        if filename is IGNORE:
            return

        customized = False
        if template in self.templates:
            # already customized by us
            customized = True
            filename = self.templates[template]['filename']
        else:
            # check if an overridable resource
            path = find_package(self.syspaths, template.filename)
            if path is None:
                # permanently ignore template
                self.templates[template] = IGNORE
                return
            filename = path.replace(os.path.sep, '.')

        customizations = self.get_customizations()
        if filename in customizations:
            filepath = customizations[filename]['filepath']
            if template not in self.templates:
                # not cached, save it
                self.templates[template] = {
                    'filename': filename,
                    'filepath': filepath,
                    'original': template.filename
                }
            else:
                self.templates[template]['filepath'] = filepath

            if template.filename != filepath:
                # if filename not same as customization, edit and return True
                template.filename = filepath
                return True
        else:
            if customized and template in self.templates:
                # revert, we had it customized but it's no longer customizations
                template.filename = self.templates[template]['original']
                del self.templates[template]
                return True


class TemplateManagerFactory(object):
    interface.implements(interfaces.ITemplateManager)

    def __init__(self):
        self.manager = _TemplateManager()

    def __call__(self, layer):
        return self.manager


TemplateManager = TemplateManagerFactory()


def mark_request(site, event):
    '''
    Mark request so each site has a unique layer `Provides` object.
    This allows us to use jbot with themes correctly without
    needing to fork/patch z3c.jbot(which would be nasty)
    '''
    if getattr(site, '_v_unique_jbot_layer', None) is None:

        class IUniqueSiteLayer(interface.Interface):
            pass

        site._v_unique_jbot_layer = IUniqueSiteLayer

    interface.alsoProvides(event.request, site._v_unique_jbot_layer)
