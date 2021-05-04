from plone.app.layout.viewlets.content import ContentRelatedItems as BaseContentRelatedItems
from Products.CMFCore.utils import getToolByName
from plone import api


class ContentRelatedItems(BaseContentRelatedItems):

    # override this method to respect castle.display_unpublished_related_items registry setting
    def related2brains(self, related):
        catalog = getToolByName(self.context, "portal_catalog")
        brains = []
        for r in related:
            path = r.to_path
            if path is None:
                # Item was deleted.  The related item should have been cleaned
                # up, but apparently this does not happen.
                continue
            # the query will return an empty list if the user
            # has no permission to see the target object
            catalog_args = {
                'path': dict(query=path, depth=0),
            }
            if not api.portal.get_registry_record(
                'plone.display_unpublished_related_items',
                default=False,
            ):
                catalog_args['review_state'] = 'published'
            brains.extend(
                catalog(**catalog_args)
            )
        return brains
