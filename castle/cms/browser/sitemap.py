from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.app.layout.sitemap import sitemap
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility


MAX_ITEMS = 50000


class SiteMapView(sitemap.SiteMapView):
    template = ViewPageTemplateFile('templates/sitemap.xml')

    def objects(self):
        """Returns the data to create the sitemap."""
        catalog = getToolByName(self.context, 'portal_catalog')
        query = {
            'sort_on': 'modified',
            'sort_limit': MAX_ITEMS,
            'sort_order': 'reverse'
        }
        utils = getToolByName(self.context, 'plone_utils')
        types = utils.getUserFriendlyTypes()
        if 'Image' in types:
            types.remove('Image')
        query['portal_type'] = types
        registry = getUtility(IRegistry)
        typesUseViewActionInListings = frozenset(
            registry.get('plone.types_use_view_action_in_listings', []))

        is_plone_site_root = IPloneSiteRoot.providedBy(self.context)
        if not is_plone_site_root:
            query['path'] = '/'.join(self.context.getPhysicalPath())

        root_page_uid = ''
        # The plone site root is not catalogued.
        if is_plone_site_root:
            loc = self.context.absolute_url()
            date = self.context.modified()
            # Comparison must be on GMT value
            modified = date.ISO8601()
            # special case, use front-page object
            try:
                page = self.context[getDefaultPage(self.context)]
                root_page_uid = IUUID(page)
                modified = page.modified().ISO8601()
                yield {
                    'loc': loc,
                    'lastmod': modified
                }
            except AttributeError:
                yield {
                    'loc': loc,
                    'lastmod': modified,
                }

        for item in catalog.searchResults(query)[:MAX_ITEMS]:  # max of 50,000 items
            if root_page_uid == item.UID or item.id == 'Members':
                continue
            loc = item.getURL()
            date = item.modified.ISO8601()
            if item.portal_type in typesUseViewActionInListings:
                loc += '/view'
            yield {
                'loc': loc,
                'lastmod': date
            }
