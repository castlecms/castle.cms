from zope.component import getAllUtilitiesRegisteredFor
from castle.cms.fragments.interfaces import IFragmentsDirectory
from castle.cms.cache import ram as cache


def getFragment(context, request, name):
    try:
        cache.get("GET_FRAGMENT_" + str(context) + str(name))
    except KeyError:
        pass
    utils = getAllUtilitiesRegisteredFor(IFragmentsDirectory)
    utils.sort(key=lambda u: u.order)
    for util in reversed(utils):
        if util.layer is not None:
            if not util.layer.providedBy(request):
                continue
        try:
            result = util.get(context, request, name)
            cache.set("GET_FRAGMENT_" + str(context) + str(name), result)
            return result
        except KeyError:
            pass
    raise KeyError(name)

def _checkFragement(util):
    pass
