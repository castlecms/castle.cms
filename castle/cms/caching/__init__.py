# -*- coding: utf-8 -*-
from plone.uuid.interfaces import IUUID
from plone.app.contenttypes.interfaces import IFile
from . import cloudflare
from App.config import getConfiguration
from castle.cms.linkintegrity import get_content_links
from plone import api
from plone.app.imaging.utils import getAllowedSizes
from plone.cachepurging.hooks import KEY
from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.interfaces import IPurger
from plone.cachepurging.utils import getPathsToPurge
from plone.cachepurging.utils import getURLsToPurge
from plone.namedfile.interfaces import IImageScaleTraversable
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.defaultpage import get_default_page
from Products.Five import BrowserView
from z3c.caching.interfaces import IPurgeEvent
from z3c.caching.interfaces import IPurgePaths
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.component import adapts
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.interface import implements
from zope.testing.cleanup import addCleanUp
from ZPublisher.interfaces import IPubSuccess
from collective.documentviewer.settings import Settings as DocViewerSettings

import atexit
import logging
import Queue
import threading


logger = logging.getLogger('castle.cms')


@adapter(IPurgeEvent)
def queuePurge(event, force=False):
    """ so this is a little wonky here...
    We need to also purge here because plone.cachepurging will only update
    paths if caching proxies are defined. The deal here is that with
    cloudflare, we do not want to define caching proxies or we may not be """

    request = getRequest()
    if request is None:
        return

    annotations = IAnnotations(request, None)
    if annotations is None:
        return

    registry = queryUtility(IRegistry)
    if registry is None:
        return

    settings = registry.forInterface(ICachePurgingSettings, check=False)
    if not settings.enabled:
        return

    # THIS IS THE OVERRIDE HERE!!!
    # the original event goes forward IF there are cache proxies defined.
    # so we check if they are NOT and then only force puring
    if bool(settings.cachingProxies) and not force:
        return

    paths = annotations.setdefault(KEY, set())
    paths.update(getPathsToPurge(event.object, request))


@adapter(IPubSuccess)
def purge(event):
    """
    Asynchronously send PURGE requests.
    this is mostly copied from plone.cachingpurging
    """
    request = event.request

    annotations = IAnnotations(request, None)
    if annotations is None:
        return

    paths = annotations.get(KEY, None)
    if paths is None:
        return

    registry = queryUtility(IRegistry)
    if registry is None:
        return

    settings = registry.forInterface(ICachePurgingSettings, check=False)
    if not settings.enabled:
        return

    if paths:
        urls = []
        cf = cloudflare.get()
        if cf.enabled:
            for path in paths:
                urls.extend(cf.getUrlsToPurge(path))

            CastlePurger.purgeAsync(urls, cf)


class CastlePurgerFactory(object):

    implements(IPurger)

    def __init__(self, backlog=200):
        self.worker = None
        self.queue = None
        self.backlog = backlog
        self.queueLock = threading.Lock()

    def purgeAsync(self, urls, purger):
        if self.worker is None:
            self.queue = Queue.Queue(self.backlog)
            self.worker = Worker(self.queue, self)
            self.worker.start()
        try:
            self.queue.put((urls, purger), block=False)
            logger.debug('Queued %s' % ','.join(urls))
        except Queue.Full:
            # Make a loud noise. Ideally the queue size would be
            # user-configurable - but the more likely case is that the purge
            # host is down.
            if not getConfiguration().debug_mode:
                logger.warning("The purge queue for the URL %s is full - the "
                               "request will be discarded.  Please check the "
                               "server is reachable, or disable this purge "
                               "host", ','.join(urls))

    def purgeSync(self, urls, purger):
        resp = purger.purge(urls)
        logger.debug('Finished purge for %s' % ','.join(urls))
        return resp

    def stopThreads(self, wait=False):
        if self.worker is None:
            return
        self.worker.stopping = True
        try:
            self.queue.put(None, block=False)
        except Queue.Full:
            # no problem - self.stopping should be seen.
            pass
        ok = True
        if wait:
            self.worker.join(5)
            if self.worker.isAlive():
                logger.warning("Cloudflare worker thread failed to terminate")
                ok = False
        return ok


class Worker(threading.Thread):
    """Worker thread for purging.
    """

    def __init__(self, queue, producer):
        self.producer = producer
        self.queue = queue
        self.stopping = False
        super(Worker, self).__init__(name="PurgeThread for castle")

    def stop(self):
        self.stopping = True

    def run(self):
        logger.debug("%s starting", self)
        # Queue should always exist!
        q = self.producer.queue
        atexit.register(self.stop)
        try:
            while not self.stopping:
                item = q.get()
                if self.stopping or item is None:  # Shut down thread signal
                    logger.debug('Stopping worker thread for '
                                 '(%s, %s).' % (self.host, self.scheme))
                    break
                urls, purger = item

                try:
                    self.producer.purgeSync(urls, purger)
                    # XXX check valid response
                except Exception:
                    logger.exception('Failed to purge %s', ','.join(urls))
        except Exception:  # FIXME: blind except
            logger.exception('Exception in worker thread '
                             'for (%s, %s)' % (self.host, self.scheme))
        logger.debug("%s terminating", self)


CastlePurger = CastlePurgerFactory()


def stopThreads():
    purger = CastlePurger
    purger.stopThreads()


addCleanUp(stopThreads)
del addCleanUp


class Purge(BrowserView):
    cf_enabled = False
    proxy_enabled = False

    def purge(self):
        site_path = '/'.join(api.portal.get().getPhysicalPath())
        cf = cloudflare.get()
        paths = []
        urls = []

        context = self.context
        dp = get_default_page(context)
        if dp:
            try:
                context = context[dp]
            except Exception:
                pass
        objs = [context]
        for ref in get_content_links(context):
            try:
                objs.append(ref.to_object)
            except Exception:
                pass

        for obj in objs:
            paths.extend(getPathsToPurge(obj, self.request))

        for path in paths:
            urls.extend(cf.getUrlsToPurge(path))

        urls = list(set(urls))

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ICachePurgingSettings, check=False)
        purger = queryUtility(IPurger)
        if purger and settings.cachingProxies:
            self.proxy_enabled = True
            for path in paths:
                for url in getURLsToPurge(path, settings.cachingProxies):
                    purger.purgeAsync(url)

        success = True
        if cf.enabled:
            self.cf_enabled = True
            resp = CastlePurger.purgeSync(urls, cf)
            success = resp.json()['success']

        nice_paths = []
        for path in paths:
            if 'VirtualHostRoot' in path:
                path = path.split('VirtualHostRoot')[-1]
            else:
                path = path[len(site_path):]
            nice_paths.append(path)

        return nice_paths, success

    def __call__(self):
        self.success = False
        self.purged = []
        authenticator = getMultiAdapter((self.context, self.request),
                                        name=u"authenticator")
        if authenticator.verify():
            self.purged, self.success = self.purge()
        return self.index()


class LeadImagePurgePaths(object):
    """Paths to purge for lead images

    Includes:

    * ${object_path}/@@images/image
    * ${object_path}/@@images/image/mini etc

    """

    implements(IPurgePaths)
    adapts(IImageScaleTraversable)

    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        if not getattr(self.context, 'image', None):
            return []

        prefix = '/' + self.context.virtual_url_path()
        paths = [prefix + '/@@images/image']

        for scale_name in getAllowedSizes().keys():
            paths.append(prefix + '/@@images/image/' + scale_name)

        return paths

    def getAbsolutePaths(self):
        return []


class DocViewerPurgePaths(object):
    """
    Paths to purge for person objects

    - purges person specific paths
    - and all objects inside folder

    """

    implements(IPurgePaths)
    adapts(IFile)

    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        if self.context.getLayout() != 'documentviewer':
            return

        site_prefix = api.portal.get().virtual_url_path()
        uid = IUUID(self.context)
        base_image_path = site_prefix + '/@@dvpdffiles/{}/{}/{}'.format(
            uid[0],
            uid[1],
            uid
        )

        settings = DocViewerSettings(self.context)
        image_format = settings.pdf_image_format or 'gif'

        paths = []
        for page_num in range(1, 5):
            for size in ('small', 'normal', 'large'):
                paths.append(base_image_path + '/{}/dump_{}.{}'.format(
                    size, page_num, image_format))

        return paths

    def getAbsolutePaths(self):
        return []
