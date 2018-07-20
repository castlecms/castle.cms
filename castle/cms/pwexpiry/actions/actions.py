from castle.cms.pwexpiry.interfaces import IExpirationCheck
from castle.cms.pwexpiry.utils import send_notification_email
from zope.interface import implements


class BaseExpiration(object):
    implements(IExpirationCheck)

    notify_on = 1

    def __init__(self, context):
        self.context = context

    def notification_action(self, userdata, days_to_expire):
        send_notification_email(userdata, days_to_expire)

    def __call__(self, days_to_expire):
        try:
            notify_on = iter(self.notify_on)
        except TypeError:
            notify_on = (self.notify_on,)

        if days_to_expire in notify_on:
            return True
        else:
            return False


class FifteenDaysBeforeExpiration(BaseExpiration):

    notify_on = 15
