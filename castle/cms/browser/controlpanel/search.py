from Products.Five import BrowserView
from plone import api


class ExclusionPanel(BrowserView):
    def get_excluded_content(self):
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(exclude_from_search=True)
        excluded_content = []
        for brain in brains:
            excluded_content.append({
                'title': brain.Title,
                'link': brain.getURL()
            })
        return excluded_content
