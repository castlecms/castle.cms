from castle.cms import cache
from castle.cms.utils import get_context_from_request
from plone import api
from Products.statusmessages.adapter import StatusMessage
from zope.i18n import translate

import time


class CastleStatusMessage(StatusMessage):
    max_messages = 10

    def __init__(self, context):  # should be request
        self.anon = api.user.is_anonymous()
        self.site_path = api.portal.get().getPhysicalPath()
        super(CastleStatusMessage, self).__init__(context)

    def get_cache_key(self):
        return '{}-{}-status-messages'.format(
            '-'.join(self.site_path[1:]),
            api.user.get_current().getId()
        )

    def add(self, text, type=u'info'):
        if self.anon:
            return super(CastleStatusMessage, self).add(text, type)

        try:
            text = translate(text)
        except Exception:
            pass

        cache_key = self.get_cache_key()
        try:
            messages = cache.get(cache_key)
        except KeyError:
            messages = []

        site_path = context_path = '/'.join(self.site_path)
        context = get_context_from_request(self.context)
        if context:
            try:
                context_path = '/'.join(context.getPhysicalPath())
            except AttributeError:
                pass

        messages.append({
            'text': text,
            'type': type,
            'timestamp': time.time(),
            'context': context_path[len(site_path):]
        })
        messages = messages[-self.max_messages:]

        # cache for 1 hour, should it be longer? shorter?
        cache.set(cache_key, messages, 1 * 60 * 60)

    addStatusMessage = add

    def get_all(self):
        cache_key = self.get_cache_key()

        try:
            messages = cache.get(cache_key)
        except KeyError:
            messages = []
        return messages
