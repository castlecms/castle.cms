from castle.cms import impersonator
from castle.cms.theming import body_xpath
from chameleon import PageTemplate
from lxml.html import fromstring
from plone import api
from plone.transformchain.interfaces import ITransform
from Products.CMFPlone.log import logger
from repoze.xmliter.serializer import XMLSerializer
from zope.component import adapter
from zope.interface import implements
from ZPublisher.interfaces import IPubEnd
from ZPublisher.interfaces import IPubStart
from castle.cms.logger import log_request

import time


@adapter(IPubStart)
def requestStart(event):
    """
    """
    req = event.request
    req.environ['__started__'] = time.time()


@adapter(IPubEnd)
def requestEnd(event):
    req = event.request
    try:
        period = time.time() - req.environ['__started__']
    except Exception:
        period = 0

    if period > 5.0:
        logger.warn('SLOW REQUEST(%i): %s' % (int(period), req.ACTUAL_URL))

    log_request(req)


_impersonator_template = PageTemplate("""
<div id="impersonator">
  <a href="${stop_url}" class="stop"><span class="glyphicon glyphicon-remove"></span></a>
  <span>This is what the website looks like to:
    <span class="anonymous" tal:condition="python: user_id == 'ANONYMOUS'">
        <span class="glyphicon glyphicon-globe"></span> Public
    </span>
    <span class="anonymous" tal:condition="python: user_id != 'ANONYMOUS'">
      <span class="glyphicon glyphicon-user"></span> ${user_name}
  </span>
</div>"""  # noqa
)  # noqa:E124


class TransformInpersonatorOutput(object):
    implements(ITransform)

    order = 10000

    def __init__(self, published, request):
        self.published = published
        self.request = request

    def transformString(self, result, encoding):
        return None

    def transformUnicode(self, result, encoding):
        return None

    def impersonator(self, result):
        if not isinstance(result, XMLSerializer):
            return
        if impersonator.ORIGINAL_USER_KEY in self.request.environ:
            if api.user.is_anonymous():
                user_id = 'ANONYMOUS'
                user_name = 'Public'
            else:
                user = api.user.get_current()
                user_id = user.getId()
                user_name = user.getProperty('fullname') or user.getId()
            html = _impersonator_template(
                user_name=user_name, user_id=user_id,
                stop_url='%s/@@impersonator?action=stop&return_url=%s' % (
                    api.portal.get().absolute_url(),
                    self.request.URL))
            dom = fromstring(html)
            body = body_xpath(result.tree)
            if len(body) > 0:
                body[0].append(dom)
        return result

    def transformIterable(self, result, encoding):
        result = self.impersonator(result) or result
        return result
