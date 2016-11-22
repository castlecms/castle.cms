# always want to be able to steal lock
from plone.protect.auto import safeWrite
from plone.locking import lockable
from plone.locking.interfaces import STEALABLE_LOCK


class TTWLockable(lockable.TTWLockable):
    def unlock(self, lock_type=STEALABLE_LOCK, stealable_only=True):
        self.clear_locks()
        locks = self._locks()
        safeWrite(locks)
        safeWrite(self.context)

    def stealable(self, lock_type=STEALABLE_LOCK):
        return True
