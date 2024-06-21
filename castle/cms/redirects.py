from castle.cms.behaviors.contentredirectable import IContentRedirectableMarker
from castle.cms.behaviors.contentredirectable import IContentRedirectable
from logging import getLogger
from ZPublisher.interfaces import IPubAfterTraversal
from zope.component import adapter

logger = getLogger('castle.cms')


@adapter(IPubAfterTraversal)
def afterTraversal(event):
    request = event.request
    published = request.get('PUBLISHED', None)
    context = getattr(published, '__parent__', None)
    if IContentRedirectableMarker.providedBy(context):
        try:
            redirect_info = IContentRedirectable(context, request)
            redirect_info.attempt_redirect()
        except Exception:
            logger.error('There was an unknown error attempting to redirect' + repr(context))
