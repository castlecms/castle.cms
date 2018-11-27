from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.WorkflowCore import WorkflowException
from Acquisition import aq_inner
from Products.CMFPlone import utils
from Products.CMFPlone.browser.interfaces import INavigationBreadcrumbs
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs
from Products.Five import BrowserView
from zope.interface import implementer
from plone import api
from castle.cms.browser.utils import Utils


@implementer(INavigationBreadcrumbs)
class PhysicalNavigationBreadcrumbs(BrowserView):

    def breadcrumbs(self):
        context = aq_inner(self.context)

        view_utils = Utils(self.context, self.request)

        crumbs = []
        while context is not None:
            if ISiteRoot.providedBy(context):
                break

            try:
                if utils.isDefaultPage(context, self.request):
                    context = utils.parent(context)
                    continue
            except AttributeError:
                break

            # Some things want to be hidden from the breadcrumbs
            if IHideFromBreadcrumbs.providedBy(context):
                context = utils.parent(context)
                continue

            item_url = view_utils.get_object_url(context)
            try:
                state = api.content.get_state(obj=context)
            except WorkflowException:
                state = None
            label = getattr(context, 'navigation_label', None)
            if not label:
                label = utils.pretty_title_or_id(context, context)
            crumbs.append({
                'absolute_url': item_url,
                'Title': label,
                'state': state
            })
            context = utils.parent(context)

        return list(reversed(crumbs))
