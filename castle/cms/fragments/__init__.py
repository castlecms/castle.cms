# Dynamic fragment template support for simple tiles
from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from castle.cms.fragments.interfaces import FRAGMENTS_DIRECTORY
from castle.cms.fragments.interfaces import IFragmentsDirectory
from castle.cms import cache
from plone import api
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import theming_policy
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.interface import implements
from zope.publisher.browser import BrowserPage

import logging
import os
import time


logger = logging.getLogger('castle')

class FileCacheFactory(object):

    CACHE_KEY = "FRAGMENTS_FILE_CACHE_FACTORY"
    
    def get_cache_storage(self):
        try:
            self.cache = cache.get(self.CACHE_KEY)
        except KeyError:
            cache.set(self.CACHE_KEY, {})
            self.cache = cache.get(self.CACHE_KEY)
        if self.cache is None:
            cache.set(self.CACHE_KEY, {})
            self.cache = cache.get(self.CACHE_KEY)
        return self.cache

    def get(self, name, filepath):
        self.get_cache_storage()
        if filepath not in self.cache:
            if not os.path.exists(filepath):
                self.cache[filepath] = {
                    'template': None,
                    'mtime': 0
                }
                cache.set(self.CACHE_KEY, self.cache)
            else:
                fi = open(filepath)
                self.cache[filepath] = {
                    'template': ZopePageTemplate(name, text=fi.read()),
                    'mtime': 0
                }
                cache.set(self.CACHE_KEY, self.cache)
                fi.close()
        return self.cache[filepath]['template']


class FileChangedCacheFactory(FileCacheFactory):
    def get(self, name, filepath):
        update = False
        try:
            data = self.get_cache_storage()[filepath]
        except KeyError:
            update = True
        if not update:
            # check mtime
            if (os.path.exists(filepath) and
                    os.path.getmtime(filepath) > data['mtime']):
                # need to update, it changed
                update = True
        if update:
            if not os.path.exists(filepath):
                self.cache[filepath] = {
                    'template': None,
                    'mtime': 9999999999
                }
                cache.set(self.CACHE_KEY, self.cache)
            else:
                fi = open(filepath)
                self.cache[filepath] = {
                    'template': ZopePageTemplate(name, fi.read()),
                    'mtime': os.path.getmtime(filepath)
                }
                cache.set(self.CACHE_KEY, self.cache)
                fi.close()
        return self.cache[filepath]['template']


class FragmentsDirectory(object):
    implements(IFragmentsDirectory)

    order = 10
    layer = None

    directory_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'templates'
    )

    def __init__(self):
        if api.env.debug_mode():
            self.cache = FileChangedCacheFactory()
        else:
            self.cache = FileCacheFactory()

    def template_factory(self, name, template):
        return ZopePageTemplate(name, text=template)

    def get(self, context, request, name):
        template_path = "%s/%s.pt" % (self.directory_path, name,)

        # Now disable the theme so we don't double-transform
        request.response.setHeader('X-Theme-Disabled', '1')

        template = self.cache.get(name, template_path)
        if template is None:
            raise KeyError(name)

        return FragmentView(
            context, request, name, 'View', template)

    def list(self):
        res = []
        if not os.path.exists(self.directory_path):
            return res
        for name in os.listdir(self.directory_path):
            if name.endswith('.pt') and name[0] != '.':
                res.append(name.replace('.pt', ''))
        return res


class ThemeFragmentsDirectory(object):
    implements(IFragmentsDirectory)

    CACHE_KEY = "THEME_FRAGMENTS_DIRECTORY"
    order = 100
    layer = None

    def __init__(self):
        self.cache = {}

    def _reset_cache(self):
        cache.set(self.CACHE_KEY, {
            'mtime': time.time(),
            'templates': {}
        })
        return cache.get(self.CACHE_KEY)

    def get_mtime(self, fi):
        try:
            return fi.lastModifiedTimestamp
        except (AttributeError, KeyError):
            return float(fi.bobobase_modification_time())

    def get_from_cache(self, policy, theme_directory, name, template_path):
        mtime = policy.getCacheStorage()['mtime']
        try:
            self.cache = cache.get(self.CACHE_KEY)
        except Exception:
            self.cache = self._reset_cache()

        key = policy.getCacheKey() + template_path
        update = False
        if mtime > self.cache['mtime']:
            # was invalidated, we need to update the template
            self.cache = self._reset_cache()
            update = True
        elif key not in self.cache['templates']:
            update = True

        if not update and key in self.cache['templates'] and api.env.debug_mode():
            # check if we need to update the cache
            try:
                template = self.cache['templates'][key]
                if self.get_mtime(theme_directory[template_path]) > template['mtime']:  # noqa
                    update = True
            except Exception:
                raise KeyError(name)

        if update:
            # use theme cache setting to see if we should re-read
            if not theme_directory.isFile(str(template_path)):
                raise KeyError(name)
            fi = theme_directory[template_path]
            template = ZopePageTemplate(name, text=theme_directory.readFile(
                str(template_path)))
            self.cache['templates'][key] = {
                'template': template,
                'mtime': self.get_mtime(fi)
            }
            cache.set(self.CACHE_KEY, self.cache)
        return self.cache['templates'][key]['template']

    def get(self, context, request, name):
        policy = theming_policy()
        theme_directory = self.get_directory(policy)

        template_path = "%s/%s.pt" % (FRAGMENTS_DIRECTORY, name)

        template = self.get_from_cache(
            policy, theme_directory, name, template_path)

        # Now disable the theme so we don't double-transform
        request.response.setHeader('X-Theme-Disabled', '1')

        return FragmentView(
            context, request, name, 'View', template)

    def get_directory(self, policy=None):
        if policy is None:
            policy = theming_policy()

        current_theme = policy.getCurrentTheme()
        if current_theme is None:
            raise KeyError()

        theme_directory = queryResourceDirectory(
            THEME_RESOURCE_NAME, current_theme)

        if theme_directory is None:
            raise KeyError()

        return theme_directory

    def list(self):
        themeDirectory = self.get_directory()
        try:
            frag_directory = themeDirectory[FRAGMENTS_DIRECTORY]
        except NotFound:
            return []
        res = []
        for name in frag_directory.listDirectory():
            if name.endswith('.pt') and name[0] != '.':
                res.append(name.replace('.pt', ''))
        return res


class FragmentView(BrowserPage):
    """View class for template-based views defined in the theme.
    When you traverse to ``..../@@fragment/foobar`` to render the view
    defined in ``fragments/foobar.pt`` in the theme, this becomes the ``view``.
    """

    CACHE_KEY="FAGMENT_VIEW_RESULTS"

    def __init__(self, context, request, name, permission, template):
        super(FragmentView, self).__init__(context, request)
        self.__name__ = name
        self._permission = permission
        self._template = template
    
    def __call__(self, options=None, *args, **kwargs):
        sm = getSecurityManager()
        if not sm.checkPermission(self._permission, self.context):
            raise Unauthorized()

        site = api.portal.get()
        site_url = site.absolute_url()
        registry = getUtility(IRegistry)
        public_url = registry.get('plone.public_url', None)
        if not public_url:
            public_url = site_url
            if not api.user.is_anonymous():
                site_url = public_url

        key = "%s::%s/%s" % (public_url, site_url, self.__name__)

        self.get()
        if key in self.cache:
            return self.cache[key]
        
        utils = getMultiAdapter((self.context, self.request),
                                name='castle-utils')
        boundNames = {
            'context': self.context,
            'request': self.request,
            'view': self,
            'portal_url': site_url,
            'public_url': public_url,
            'site_url': site_url,
            'registry': registry,
            'portal': site,
            'utils': utils
        }
        if options is not None:
            boundNames.update(options)

        zpt = self._template.__of__(self.context)
        try:
            result = zpt._exec(boundNames, args, kwargs)
            self.set(key, result)
            return result
        except NotFound as e:
            # We don't want 404's for these - they are programming errors
            raise Exception(e)
        
    def get(self):
        try:
            self.cache = cache.get(self.CACHE_KEY)
        except KeyError:
            self.cache = {}
            cache.set(self.CACHE_KEY, self.cache)

    def set(self, key, value):
        self.cache[key] = value
        cache.set(self.CACHE_KEY, self.cache, expire=60*10)
