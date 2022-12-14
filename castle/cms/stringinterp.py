from castle.cms import subscribe
from plone.stringinterp import _
from plone.stringinterp.adapters import BaseSubstitution
from plone.stringinterp.dollarReplace import LazyDict
from plone.stringinterp.interfaces import IStringInterpolator
from Products.CMFCore.interfaces import IContentish
import string
from zope.component import adapts, adapter
from zope.interface import implementer


@adapter(IContentish)
class SubscriberMailAddressSubstitution(BaseSubstitution):
    pass


class SubscriberCategoryEmailSubstitution(BaseSubstitution):
    category = _(u'Category Subscribers')
    description = _(
        u'Subscriber E-Mail addresses for category "x", managed under '
        u'Site Setup -> Announcements -> Manage Categories (ex: '
        u'"category_emails_for_news"). NOTE: "x" is case-insensitive and '
        u'spaces should be replaced with underscores, ex: "Meeting Minutes" '
        u'would be "${category_emails_for_meeting_minutes}"')

    def __init__(self, context, category=None):
        super(SubscriberCategoryEmailSubstitution, self).__init__(context)
        self.category = category.lower().replace(" ", "_")

    def safe_call(self):
        emails = []
        for subscriber in subscribe.all():
            if 'categories' not in subscriber:
                continue
            categories = subscriber['categories']
            for c in categories:
                if c.lower().replace(" ", "_") == self.category:
                    email = subscriber.get("email", None)
                    if email is not None:
                        emails.append(email)
                    break
        return u', '.join(emails)


class CastleLazyDict(LazyDict):
    def __getitem__(self, key):
        if key.startswith("category_emails_for_"):
            category = key[20:]
            res = self._cache.get(key)
            if res is None:
                res = SubscriberCategoryEmailSubstitution(self.context, category=category)()
            return res
        else:
            return super(CastleLazyDict, self).__getitem__(key)


@implementer(IStringInterpolator)
class CastleInterpolator(object):
    adapts(IContentish)

    def __init__(self, context):
        self._cldict = CastleLazyDict(context)

    def __call__(self, s):
        return string.Template(s).safe_substitute(self._cldict)
