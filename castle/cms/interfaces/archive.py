from zope.interface import Interface


class IArchiveContentTransformer(Interface):
    def __init__(archiver):
        pass

    def __call__(dom):
        pass


class IArchiveManager(Interface):
    pass
