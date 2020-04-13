from .layers import ICastleLayer

class ICastleThemingCacheReset(ICastleLayer):
    """
    Clears theming files outside of the local threads.
    """

    def invalidateOtherCaches(self):
        """
        Calls upon this will clear out the other caches containing theming files.
        """
