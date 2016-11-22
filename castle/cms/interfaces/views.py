from zope.interface import Interface


class ITileView(Interface):

    def __init__(self, tile):
        pass


class ISecureLoginAllowedView(Interface):
    """
    marker interface to describe a view that is allowed to be rendered
    """
