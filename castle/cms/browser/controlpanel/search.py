from Products.Five import BrowserView
from plone import api


class ExclusionPanel(BrowserView):
    def get_excluded_content(self):
        catalog = api.portal.get_tool('portal_catalog')
        excluded_content = catalog(exclude_from_search=True)
        return excluded_content
