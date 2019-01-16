import hashlib
import json
import random
import time
from datetime import datetime
from hashlib import sha256 as sha

from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from plone import api
from ZODB.POSException import ConflictError


try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    using_sysrandom = False


SECRET = random.randint(0, 1000000)


def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Returns a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(
            sha(
                "%s%s%s" % (
                    random.getstate(),
                    time.time(),
                    SECRET)
                ).digest())  # noqa
    return ''.join([random.choice(allowed_chars) for i in range(length)])


def make_random_key(length=150, prefix=''):
    if prefix:
        prefix = str(prefix) + '-'
    hashed = '%s%s' % (
        hashlib.sha1(str(get_random_string(length)).encode('utf-8')).hexdigest()[:5],  # noqa
        str(datetime.now().microsecond)
    )
    return prefix + hashlib.sha1(hashed.encode('utf-8')).hexdigest()[:length]


def retriable(count=3, sync=False, reraise=True, on_retry_exhausted=None):

    def decorator(func):
        def wrapped(*args, **kwargs):
            retried = 0
            if sync:
                try:
                    api.portal.get()._p_jar.sync()
                except Exception:
                    pass
            while retried < count:
                try:
                    return func(*args, **kwargs)
                except ConflictError:
                    retried += 1
                    try:
                        api.portal.get()._p_jar.sync()
                    except Exception:
                        if retried >= count:
                            if on_retry_exhausted is not None:
                                on_retry_exhausted(*args, **kwargs)
                            if reraise:
                                raise
        return wrapped
    return decorator


def get_ip(req):
    ip = req.get('HTTP_CF_CONNECTING_IP')
    if not ip:
        ip = req.get('HTTP_X_FORWARDED_FOR')
    if not ip:
        ip = req.get('HTTP_X_REAL_IP')
    if not ip:
        ip = req.get('REMOTE_ADDR')
    return ip


def normalize_url(url):
    url = url.split('#')[0]
    if url.startswith('data:'):
        return None
    return url


def strings_differ(string1, string2):
    """Check whether two strings differ while avoiding timing attacks.

    This function returns True if the given strings differ and False
    if they are equal.  It's careful not to leak information about *where*
    they differ as a result of its running time, which can be very important
    to avoid certain timing-related crypto attacks:

        http://seb.dbzteam.org/crypto/python-oauth-timing-hmac.pdf

    """
    if len(string1) != len(string2):
        return True

    invalid_bits = 0
    for a, b in zip(string1, string2):
        invalid_bits += a != b

    return invalid_bits != 0


def _customhandler(obj):
    if type(obj) == DateTime:
        return obj.ISO8601()
    if type(obj) == PersistentList:
        return list(obj)
    if type(obj) == PersistentDict:
        return dict(obj)
    if type(obj) == OOBTree:
        return dict(obj)
    raise TypeError(
        "Unserializable object {} of type {}".format(obj, type(obj)))


def json_dumps(data):
    return json.dumps(data, default=_customhandler)
