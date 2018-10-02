# implements site subscription technology
from time import time

from BTrees.OOBTree import OOBTree
from castle.cms.utils import make_random_key
from persistent.mapping import PersistentMapping
from plone import api


class InvalidEmailException(KeyError):
    pass


class InvalidCodeException(Exception):
    pass


class SubscriptionStorage(object):

    def __init__(self):
        self.site = api.portal.get()
        try:
            self._data = self.site._subscribers
        except AttributeError:
            self._data = OOBTree()
            self.site._subscribers = self._data

    def add(self, email, data=None):
        email = email.lower()
        if data is None:
            data = {}
        data.update({
            'created': time(),
            'code': make_random_key(100),
            'confirmed': False,
            'phone_number_confirmed': False,
            'email': email
        })
        self._data[email] = PersistentMapping(data)
        return data

    def remove(self, email):
        if email.lower() in self._data:
            del self._data[email.lower()]

    def get(self, email):
        return self._data.get(email.lower())


def get(email):
    storage = SubscriptionStorage()
    return storage.get(email)


def remove(email):
    storage = SubscriptionStorage()
    return storage.remove(email)


def register(email, data):
    storage = SubscriptionStorage()
    return storage.add(email, data)


def confirm(email, code):
    storage = SubscriptionStorage()
    subscriber = storage.get(email)
    if not subscriber:
        raise InvalidEmailException(email)
    if subscriber['code'] != code:
        raise InvalidCodeException()
    subscriber['confirmed'] = True


def confirm_phone_number(email, code):
    storage = SubscriptionStorage()
    subscriber = storage.get(email)
    if not subscriber:
        raise InvalidEmailException(email)
    if len(code) < 6:
        raise InvalidCodeException()
    if not subscriber['code'].endswith(code):
        raise InvalidCodeException()
    subscriber['phone_number_confirmed'] = True


def get_subscriber(email):
    storage = SubscriptionStorage()
    return storage.get(email)


def all():
    storage = SubscriptionStorage()
    for subscriber in storage._data.values():
        if subscriber.get('confirmed'):
            yield subscriber


def get_phone_numbers():
    numbers = []
    storage = SubscriptionStorage()
    for subscriber in storage._data.values():
        number = subscriber.get('phone_number')
        if (number and subscriber.get('phone_number_confirmed', False) and
                subscriber.get('confirmed')):
            numbers.append(number)
    return numbers


def get_email_addresses():
    storage = SubscriptionStorage()
    result = []
    for email, subscriber in storage._data.items():
        if subscriber.get('confirmed'):
            result.append(email)

    return result
