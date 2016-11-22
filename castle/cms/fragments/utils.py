from zope.component import getAllUtilitiesRegisteredFor
from castle.cms.fragments.interfaces import IFragmentsDirectory


def getFragment(context, request, name):
    utils = getAllUtilitiesRegisteredFor(IFragmentsDirectory)
    utils.sort(key=lambda u: u.order)
    for util in reversed(utils):
        if util.layer is not None:
            if not util.layer.providedBy(request):
                continue
        try:
            return util.get(context, request, name)
        except KeyError:
            pass
    raise KeyError(name)
