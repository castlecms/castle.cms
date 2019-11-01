from plone.memoize.interfaces import ICacheChooser
from plone.memoize.ram import choose_cache as base_choose_cache
from plone.memoize.ram import AbstractDict
from zope.interface import directlyProvides

import cPickle
import os
import redis
import threading

from zope import ramcache
import logging

logger = logging.getLogger(__name__)

global_ram_cache = ramcache.ram.RAMCache()
global_ram_cache.update(maxAge=60 * 10)


thread_local = threading.local()


def redis_installed():
    try:
        return isinstance(get_client(), RedisAdapter)
    except Exception:
        return False


class RedisAdapter(AbstractDict):
    """
    Also cache ON the request to deal with some cache calls that are done
    multiple times per request
    """

    def __init__(self, client, globalkey=''):
        self.client = client
        self.globalkey = globalkey and '%s:' % globalkey or ''

    def _make_key(self, source):
        if isinstance(source, unicode):
            source = source.encode('utf-8')
        return source

    def get_key(self, key):
        return self.globalkey + self._make_key(key)

    def __getitem__(self, key):
        if 'plone.app.theming.plugins' in key:
            # bit of a hack here... We don't want theming plugins to be
            # contacting redis for every call. This is just a utility lookup
            # so it is cheaper to do it in code than cache with redis and
            # potentially have the network traffic
            raise KeyError(key)

        cached_value = self.client.get(key)
        if cached_value is None:
            raise KeyError(key)
        else:
            val = cPickle.loads(cached_value)
            return val

    def __setitem__(self, key, value):
        cache_key = self.get_key(key)
        try:
            cached_value = cPickle.dumps(value)
            self.client.set(cache_key, cached_value)
        except cPickle.PicklingError:
            pass


def get_client(fun_name=''):
    server = os.environ.get('REDIS_SERVER', None)
    if server is None:
        if not getattr(get_client, '___default_warned', True):
            logger.warning(
                "Not using redis; REDIS_SERVER environment variable is undefined")
            get_client.___default_warned = False
        return base_choose_cache(fun_name)

    client = getattr(thread_local, "client", None)
    if client is None:
        server = os.environ.get("REDIS_SERVER", "127.0.0.1:6379")
        logger.debug("using REDIS_SERVER %s" % server)
        host, _, port = server.partition(':')
        client = redis.StrictRedis(host=host, port=int(port), db=0)
        try:
            client.get('test-key')
            thread_local.client = client
        except redis.exceptions.ConnectionError:
            if not getattr(get_client, '___connect_warned', True):
                logger.warning("unable to connect to redis")
                get_client.___connect_warned = False
            return base_choose_cache(fun_name)
    return RedisAdapter(client, fun_name)


directlyProvides(get_client, ICacheChooser)


def get(name):
    return get_client()[name]


def set(name, value, expire=None):
    client = get_client()
    client[name] = value
    if expire and isinstance(client, RedisAdapter):
        try:
            key = client.get_key(name)
            client = client.client
            client.expire(key, expire)
        except AttributeError:
            pass


def delete(name):
    try:
        get_client().client.delete(name)
    except AttributeError:
        pass


MARKER = object()


class RamCache(object):
    def get(self, name):
        value = global_ram_cache.query('', {'key': name}, default=MARKER)
        if value is MARKER:
            raise KeyError(name)
        return value

    def set(self, name, value):
        global_ram_cache.set(value, '', {'key': name})


ram = RamCache()
