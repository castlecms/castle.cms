from zope.component import getAllUtilitiesRegisteredFor
from castle.cms.fragments.interfaces import IFragmentsDirectory
from castle.cms.fragments import FragmentView
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate

import logging


logger = logging.getLogger('castle.cms')


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
    logger.warn('Could not get fragment {0}'.format(name))
    template = ZopePageTemplate('missing',
                                text='<!-- fragment with missing template -->')
    return FragmentView(context, request, name, 'View', template)
