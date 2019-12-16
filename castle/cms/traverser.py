from zope.publisher.interfaces import IPublishTraverse
from ZPublisher.BaseRequest import DefaultPublishTraverse
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.publisher.interfaces.http import IHTTPRequest
from zope.component import adapts
from zope.interface import implements
from plone.memoize.forever import memoize
from plone import api


class IsolatedSiteTraverser(DefaultPublishTraverse):
    """
    This traverser is applied only once you traverse an IIsolatedObject.
    This traverser look first if one of the names to be traversed matches
    with one of the root isolated objects. Then
        * if None of them match then it use the default traverser (see DefaultPublishTraverse) ;
        * if one of them match, we mark the request as being a potentially bad
          request and check if the first name we are traversing is one of the
          isolated objects.
    """
    adapts(IPloneSiteRoot, IHTTPRequest)
    implements(IPublishTraverse)

    @memoize
    def get_site_objects(self):
        """
        Return the objects on the Zope root (we are assuming here that your sites
        are on the top level) that have to be isolated from each others
        """
        return frozenset([id for id, obj in api.portal.get().aq_parent.objectItems() if IPloneSiteRoot.providedBy(obj)])  # noqa

    def publishTraverse(self, request, name):
        namesToTraverse = frozenset([name] + self.request['TraversalRequestNameStack'])
        sites = self.get_site_objects()
        if namesToTraverse.intersection(sites) and name in sites:
            raise KeyError(name)
        else:
            return super(IsolatedSiteTraverser, self).publishTraverse(request, name)
