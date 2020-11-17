from plone.memoize.view import memoize
from castle.cms.utils import parse_query_from_data
from plone.memoize.view import memoize_contextless
from plone.tiles import Tile
from plone.tiles.interfaces import IPersistentTile
from Products.CMFCore.utils import getToolByName
from urllib import quote_plus
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.interface import implements
from zope.security import checkPermission
from castle.cms.tiles.views import getTileView

import json
import logging
import traceback


logger = logging.getLogger('castle.cms')


def _one(val):
    if type(val) in (list, set, tuple):
        if len(val) > 0:
            return val[0]
    return val


class BaseTile(Tile):
    global_editable = False
    edit_label = 'Tile'
    edit_permission = 'cmf.ModifyPortalContent'
    wrap = True

    def get_focal_point(self):
        focal = self.data.get('override_focal_point')
        if not focal:
            return
        try:
            focal = json.loads(focal)
            if len(focal) == 2:
                return focal
        except Exception:
            pass

    @property
    def title(self):
        return self.data.get('title', None)

    @property
    def more_link(self):
        return _one(self.data.get('more_link', None))

    @property
    def more_text(self):
        return self.data.get('more_text', None)

    @property
    @memoize
    def site(self):
        return getSite()

    @property
    @memoize
    def catalog(self):
        return getToolByName(self.site, 'portal_catalog')

    @property
    @memoize_contextless
    def utils(self):
        return getMultiAdapter((self.context, self.request),
                               name="castle-utils")

    @property
    def edit_url(self):
        url = '%s/@@edit-tile/%s/%s' % (
            self.context.absolute_url(), self.__name__, self.id or ''
        )
        if IPersistentTile.providedBy(self):
            url += '?' + self.request.environ.get('QUERY_STRING') or ''
        return url

    @property
    def view_url(self):
        url = '%s/@@%s/%s' % (
            self.context.absolute_url(), self.__name__, self.id or ''
        )
        if IPersistentTile.providedBy(self):
            if hasattr(self.request, 'tile_data'):
                qs = []
                for k, v in self.request.tile_data.items():
                    if not v or k == 'X-Tile-Persistent':
                        continue
                    if isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                for subk, subv in item.items():
                                    qs.append((
                                        '%s.%s:records' % (k, subk),
                                        str(subv)
                                    ))
                            else:
                                qs.append((
                                    '%s:records' % k,
                                    str(subv)
                                ))
                    else:
                        qs.append((k, str(v)))
                qs = '&'.join([k + '=' + quote_plus(v) for k, v in qs])
            else:
                qs = self.request.environ.get('QUERY_STRING') or ''
            url += '?' + qs
        return url

    def __call__(self):
        self.request.response.setHeader('X-Theme-Disabled', '1')
        try:
            res = self.render()
            if self.global_editable and checkPermission('cmf.ModifyPortalContent', self.context):
                # wrap with tile url div
                config = json.dumps({
                    'label': self.edit_label,
                    'url': self.view_url,
                    'editUrl': self.edit_url
                })
                res = """
<div class="castle-tile-wrapper pat-edittile"
     data-pat-edittile='%s'>%s</div>""" % (
                    config, res)
            else:
                if self.wrap:
                    res = '<div class="castle-tile-wrapper">%s</div>' % res
            return '<html><body>' + res + '</body></html>'
        except Exception:
            path = ['']
            if hasattr(self.context, 'getPhysicalPath'):
                path = self.context.getPhysicalPath()
            logger.error(
                'Error rendering tile on context: %s, url: %s, data: %s,\n%s' % (
                    '/'.join(path),
                    self.request.ACTUAL_URL,
                    repr(self.data),
                    traceback.format_exc()))
            return """<html><body>
<p class="tileerror">
  We apologize, there was an error rendering this snippet
</p></body></html>"""

    def render(self):
        return self.index()


class DisplayTypeTileMixin(object):
    display_type_name = ''
    display_type_default = 'default'
    display_type_fallback_view = None

    def render_display(self):
        view = getTileView(
            self.context, self.request, self.display_type_name,
            self.data.get('display_type', self.display_type_default) or self.display_type_default,
            default=self.display_type_default)
        if view is None:
            if self.display_type_fallback_view:
                view = self.display_type_fallback_view(self.context, self.request)
            else:
                return '<div>Warning: No display found</div>'

        view.tile = self
        return view()


class ContentTile(BaseTile):
    implements(IPersistentTile)
    default_display_fields = ('title', 'image', 'description')
    sort_limit = 1

    def render(self):
        return self.index()

    @property
    def content(self):
        if self.data.get('use_query') in ('True', True, 'true'):
            catalog = getToolByName(self.context, 'portal_catalog')
            items = catalog(**self.query)
            if len(items) > 0:
                return items[0].getObject()
        else:
            return self.utils.get_object(self.data['content'][0])

    @property
    def query(self):
        parsed = parse_query_from_data(self.data, self.context)
        if self.sort_limit:
            parsed['sort_limit'] = self.sort_limit
        return parsed

    @property
    def display_fields(self):
        df = self.data.get('display_fields', None)
        if df is None:
            df = self.default_display_fields
        return df


class BaseImagesTile(ContentTile):
    implements(IPersistentTile)
    sort_limit = 0

    def get_image_data_from_brain(self, brain):
        base_url = brain.getURL()
        return {
            'high': '%s/@@images/image/high' % base_url,
            'large': '%s/@@images/image/large' % base_url,
            'medium': '%s/@@images/image/preview' % base_url,
            'thumb': '%s/@@images/image/thumb' % base_url,
            'original': base_url,
            'title': brain.Title,
            'description': brain.Description or '',
            'link': '%s/view' % base_url
        }

    def get_image_data(self, im):
        base_url = im.absolute_url()
        related = self.get_related(im) or im
        return {
            'high': '%s/@@images/image/high' % base_url,
            'large': '%s/@@images/image/large' % base_url,
            'medium': '%s/@@images/image/preview' % base_url,
            'thumb': '%s/@@images/image/thumb' % base_url,
            'original': base_url,
            'title': im.Title(),
            'description': im.Description() or '',
            'link': '%s/view' % related.absolute_url()
        }

    def get_images_in_folder(self, brain):
        if brain.portal_type == 'Folder':
            # get contents
            folder = brain.getObject()
            images = folder.getFolderContents()
            results = []
            for image in images:
                if image.portal_type == 'Image':
                    results.append(self.get_image_data_from_brain(image))
                else:
                    obj = image.getObject()
                    if hasattr(obj, 'image') and hasattr(obj.image, 'contentType'):
                        results.append(self.get_image_data(obj))
            return results
        else:
            return [self.get_image_data_from_brain(brain)]

    @property
    def images(self):
        if self.data.get('use_query') in ('True', True, 'true'):
            return self.query_images()
        else:
            return self.get_selected_images()

    def query_images(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        results = []
        query = self.query
        query['hasImage'] = True
        for brain in catalog(**query):
            results.append(self.get_image_data_from_brain(brain))
        return results

    def get_selected_images(self):
        results = []
        brains = list(self.catalog(UID=self.data.get('images', [])))
        # we need to order this since catalog results are not ordered
        for uid in self.data.get('images') or []:
            found = False
            for brain in brains:
                if brain.UID == uid:
                    found = brain
                    break
            if not found:
                continue
            brains.remove(found)
            if found.is_folderish:
                results.extend(self.get_images_in_folder(brain))
            else:
                results.append(self.get_image_data_from_brain(found))
        return results

    def get_related(self, obj):
        try:
            return obj.relatedItems[0]
        except Exception:
            return None
