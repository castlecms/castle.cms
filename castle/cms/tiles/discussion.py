from zope.component import getUtility
from plone import api
from Acquisition import aq_inner
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from plone.app.standardtiles import discussion

DISQUS_CODE = """
<div id="disqus_thread"></div>
<script>
  var disqus_config = function () {
    this.page.url = "%(url)s";
    this.page.identifier = "%(uid)s";
  };
  (function() {
    var d = document, s = d.createElement('script');
    s.src = '//%(shortname)s.disqus.com/embed.js';

    s.setAttribute('data-timestamp', +new Date());
    (d.head || d.body).appendChild(s);
  })();
</script>
"""


class DiscussionTile(discussion.DiscussionTile):

    def __call__(self):
        context = aq_inner(self.context)
        convo = context.restrictedTraverse('@@conversation_view', None)
        if not convo or not convo.enabled():
            return u'<html></html>'

        registry = getUtility(IRegistry)
        try:
            disqus_shortname = registry['plone.disquis_shortname']
        except Exception:
            disqus_shortname = None

        if not disqus_shortname:
            return super(DiscussionTile, self).__call__()

        url = self.context.absolute_url()
        public_url = registry.get('plone.public_url', None)
        if public_url:
            url = url.replace(
                api.portal.get().absolute_url(),
                public_url.rstrip('/') + '/')

        return DISQUS_CODE % {
            'url': url,
            'uid': IUUID(self.context),
            'shortname': disqus_shortname
        }
