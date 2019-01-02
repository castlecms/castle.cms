from Products.Five import BrowserView
from castle.cms.lockout import LockoutManager


class LockedOutView(BrowserView):

    def __call__(self):
        manager = LockoutManager(self.context, self.request.get('username'))
        self.attempts = manager.get_attempts_this_window()
        self.manager = manager
        return self.index()


class DisabledUserView(BrowserView):

    def __call__(self):
        return self.index()
