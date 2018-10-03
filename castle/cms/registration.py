from time import time

from BTrees.OOBTree import OOBTree
from castle.cms.utils import make_random_key


class RegistrationStorage(object):

    attr_name = '_registration_confirmations'

    def __init__(self, context):
        self.context = context
        try:
            self._data = getattr(context, self.attr_name)
        except AttributeError:
            self._data = OOBTree()
            setattr(context, self.attr_name, self._data)

    def add(self, email, data=None):
        self.clean()
        email = email.lower()
        if data is None:
            data = {}
        data.update({
            'created': time(),
            'code': make_random_key(100)
        })
        self._data[email] = data
        return data

    def remove(self, email):
        if email.lower() in self._data:
            del self._data[email.lower()]

    def get(self, email):
        return self._data.get(email.lower())

    def clean(self):
        now = time()
        delete = []
        for email, item in self._data.items():
            if not item:
                delete.append(email)
                continue
            created = item['created']
            # delete all older than 1 hour
            if int((now - created) / 60 / 60) > 1:
                delete.append(email)
        for code in delete:
            del self._data[code]


class RegistrationReviewStorage(RegistrationStorage):
    attr_name = '_registrations_under_review'
