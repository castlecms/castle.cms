from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.app.layout.sitemap import sitemap
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility


MAX_ITEMS = 50000


class SiteMapView(sitemap.SiteMapView):
    template = ViewPageTemplateFile('templates/sitemap.xml')

    def objects(self):
        """Returns the data to create the sitemap."""
        registry = getUtility(IRegistry)
        catalog = api.portal.get_tool('portal_catalog')
        query = {
            'sort_on': 'modified',
            'sort_limit': MAX_ITEMS,
            'sort_order': 'reverse',
            'review_state': 'published'
        }
        utils = api.portal.get_tool('plone_utils')
        types = utils.getUserFriendlyTypes()
        if 'Image' in types:
            types.remove('Image')
        query['portal_type'] = types
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

        for brain in catalog.searchResults(query)[:MAX_ITEMS]:  # max of 50,000 items
            pub_in_priv = registry.get('plone.allow_public_in_private_container', False)
            if root_page_uid == brain.UID or brain.id == 'Members' or \
                    (brain.has_private_parents and not pub_in_priv):
                continue
            loc = brain.getURL()
            date = brain.modified.ISO8601()
            if brain.portal_type in typesUseViewActionInListings:
                loc += '/view'
            yield {
                'loc': loc,
                'lastmod': date
            }
