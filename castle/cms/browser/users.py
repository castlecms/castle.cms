from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from plone.app.users.browser import membersearch
from plone import api


class MemberSearchForm(membersearch.MemberSearchForm):

    def __call__(self):
        registry = getUtility(IRegistry)
        view_about = registry.get('plone.allow_anon_views_about', False)
        if not view_about and api.user.is_anonymous():
            return self.request.response.redirect(api.portal.get().absolute_url())
        return super(MemberSearchForm, self).__call__()
