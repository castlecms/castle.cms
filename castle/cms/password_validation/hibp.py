from castle.cms.interfaces.passwordvalidation import ICustomPasswordValidator
from plone import api
from zope.interface import implementer
import hashlib
import urllib2

from castle.cms import _


@implementer(ICustomPasswordValidator)
class HaveIBeenPwned(object):
    """ Checks if the password has already been used
    by iterating over the memberdata property password_history_size.
    """

    def __init__(self, context):
        self.context = context

    def validate(self, password, data):
        # Permit empty passwords here to allow registration links.
        # Plone will force the user to set one.
        if password is None:
            return None

        if api.user.is_anonymous():
            # No check for registrations.
            return None

        sha = hashlib.sha1(password).hexdigest()
        needle = sha[5:]
        url = 'https://api.pwnedpasswords.com/range/' + sha[:5]
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'castle.cms')
        haystacks = urllib2.urlopen(req).readlines()
        for haystack in haystacks:
            if needle == haystack[:35]:
                return _(
                    u'Password must not appear on "Have I Been Pwned?" database',
                    default=u'Password must not appear on "Have I Been Pwned?" database'
                )
        return None
