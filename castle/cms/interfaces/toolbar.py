from zope.interface import Attribute
from zope.interface import Interface


class IToolbarModifier(Interface):
    layer = Attribute('layer to be used with')
    order = Attribute('order should be run with')

    def __call__(menu):
        pass
