from DateTime import DateTime
from copy import deepcopy
from persistent.dict import PersistentDict
from lxml import etree
from lxml.html import tostring
from repoze.xmliter.utils import getHTMLSerializer
from castle.cms import theming
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from castle.cms.tiles import meta
from plone import api
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX as TILE_ANNOTATIONS_KEY_PREFIX
from plone.tiles.interfaces import IPersistentTile
from plone.tiles.interfaces import ITileDataManager
from plone.tiles.interfaces import ITileType
from plone.uuid.interfaces import IUUIDGenerator
from Products.Five import BrowserView
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.event import notify
from zope.interface import alsoProvides
from zope.lifecycleevent import ObjectRemovedEvent
from castle.cms.events import MetaTileEditedEvent
import urllib

import json


class MetaTileManager(BrowserView):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        if self.request.get('action') == 'addtile':
            self.add_tile()
        elif self.request.get('action') == 'deletetile':
            self.delete_tile()
        elif self.request.get('action') == 'moveup':
            self.move_up()
        elif self.request.get('action') == 'movedown':
            self.move_down()
        elif self.request.get('action') == 'mode':
            self.change_mode()
        elif self.request.get('action') == 'copymeta':
            # XXX disabling working copy support
            return self.copy_meta()
        elif self.request.get('action') == 'savecopy':
            return self.save_copy()
        elif self.request.get('action') == 'cancelcopy':
            return self.cancel_copy()
        return self.info()

    def copy_meta(self):
        # XXX disable working copy support
        return json.dumps({
            'newId': self.request.get('metaId'),
            'success': True,
            'locked': False
        })
        _id = self.request.get('metaId')
        copy_id = self.get_working_copy_meta_id()
        annotations = IAnnotations(self.context)
        data = annotations.get(TILE_ANNOTATIONS_KEY_PREFIX + '.' + _id)
        if not data:
            data = PersistentDict()

        if ('locked' in data and
                self.request.get('override', '').lower() not in ('y', 'yes', '1',
                                                                 'true', 't') and
                api.user.get_current().getId() != data['locked']['user']):
            return json.dumps({
                'locked': True,
                'success': False,
                'lock_data': data['locked']
            })

        if TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id in annotations:
            # cut out, we're good, resume existing
            return json.dumps({
                'newId': copy_id,
                'success': True,
                'locked': False
            })

        version_key = self.get_working_copy_key()
        tile_mapping = {}
        new_tiles = []
        for tile in data.get('tiles', []):
            # make copies of all the tiles
            tile_id = tile['id']
            copy_tile_id = '{}-{}'.format(tile_id, version_key)
            tile_data = annotations.get(TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id)
            if tile_data:
                annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_tile_id] = deepcopy(tile_data)
            new_tile_info = deepcopy(tile)
            new_tile_info['id'] = copy_tile_id
            new_tiles.append(new_tile_info)
            tile_mapping[tile_id] = copy_tile_id

        new_data = PersistentDict(dict(data))
        new_data.update({
            'tiles': new_tiles,
            'mapping': tile_mapping
        })
        data.update({
            'locked': {
                'when': DateTime().ISO8601(),
                'user': api.user.get_current().getId()
            }
        })
        annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id] = new_data

        return json.dumps({
            'newId': copy_id,
            'success': True,
            'locked': False
        })

    def save_copy(self):
        # XXX disable working copy support
        return json.dumps({
            'success': True
        })
        annotations = IAnnotations(self.context)
        _id = self.request.get('metaId')
        copy_id = self.get_working_copy_meta_id()
        existing_data = annotations.get(TILE_ANNOTATIONS_KEY_PREFIX + '.' + _id, {})
        new_data = annotations.get(TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id)

        existing_tiles = existing_data.get('tiles', [])
        new_tiles = new_data.get('tiles', [])
        new_tile_ids = [t['id'] for t in new_tiles]
        # tile id: copy tile id
        tile_mapping = new_data.get('mapping', {})
        # copy tile id: tile id
        tile_mapping_reversed = {v: k for k, v in tile_mapping.items()}

        # remove deleted tiles
        for existing_tile in existing_tiles:
            tile_id = existing_tile['id']
            copy_tile_id = tile_mapping.get(tile_id, None)
            if copy_tile_id not in new_tile_ids:
                # was removed, so we delete the data associated with it
                if TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id in annotations:
                    del annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id]

        # overwrite new tile data
        for copy_tile in new_tiles:
            copy_tile_id = copy_tile['id']
            if copy_tile_id in tile_mapping_reversed:
                tile_id = tile_mapping_reversed[copy_tile_id]
                # move tile data onto correct key
                if TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_tile_id in annotations:
                    annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id] = \
                        annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_tile_id]
                    del annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_tile_id]
                    copy_tile['id'] = tile_id

        # now save the meta tile
        annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + _id] = \
            annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id]
        del annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id]

        # also, destory any other active edits for this slot
        for key in list(annotations.keys()):
            if key.startswith(TILE_ANNOTATIONS_KEY_PREFIX + '.' + _id + '-copy-'):
                # also delete tiles referenced here.
                if key not in annotations:
                    continue
                data = annotations[key]
                for tile in data.get('tiles', []):
                    # since these are all copied tiles or new tiles, we can remove
                    tile_id = tile['id']
                    if TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id in annotations:
                        del annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id]
                del annotations[key]

        notify(MetaTileEditedEvent(self.context, _id))

        return json.dumps({
            'success': True
        })

    def cancel_copy(self):
        annotations = IAnnotations(self.context)

        _id = self.request.get('metaId')
        copy_id = self.get_working_copy_meta_id()
        existing_data = annotations.get(TILE_ANNOTATIONS_KEY_PREFIX + '.' + _id, {})
        new_data = annotations.get(TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id, {})

        for tile in new_data.get('tiles', []):
            tile_id = tile['id']
            # since these are all copied tiles or new tiles, we can remove
            if TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id in annotations:
                del annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile_id]
        if TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id in annotations:
            del annotations[TILE_ANNOTATIONS_KEY_PREFIX + '.' + copy_id]

        if 'locked' in existing_data:
            del existing_data['locked']

        return json.dumps({
            'success': True
        })

    def get_working_copy_key(self):
        user = api.user.get_current()
        return 'copy-{}'.format(user.getId())

    def get_working_copy_meta_id(self):
        # XXX disabling locking support
        _id = self.request.get('metaId')
        return _id
        return '{}-{}'.format(_id, self.get_working_copy_key())

    def get_tile(self, tile_type, _id):
        tile = getMultiAdapter((self.context, self.request), name=tile_type)
        alsoProvides(tile, IPersistentTile)
        tile.id = _id
        tile.__name__ = tile_type
        return tile

    def get_meta_data_manager(self):
        _id = self.get_working_copy_meta_id()
        meta_tile = meta.getTile(self.context, self.request, _id)
        return ITileDataManager(meta_tile)

    def move_up(self):
        idx = int(self.request.get('idx'))
        if idx == 0:
            return
        meta_data_manager = self.get_meta_data_manager()
        meta_data = meta_data_manager.get()
        tiles = meta_data['tiles']
        tomove = tiles[idx - 1]
        tiles[idx - 1] = tiles[idx]
        tiles[idx] = tomove

        meta_data['tiles'] = tiles
        meta_data_manager.set(meta_data)

    def move_down(self):
        idx = int(self.request.get('idx'))
        meta_data_manager = self.get_meta_data_manager()
        meta_data = meta_data_manager.get()
        tiles = meta_data['tiles']

        if idx >= len(tiles) - 1:
            return

        tomove = tiles[idx + 1]
        tiles[idx + 1] = tiles[idx]
        tiles[idx] = tomove

        meta_data['tiles'] = tiles
        meta_data_manager.set(meta_data)
        pass

    def add_tile(self):
        generator = getUtility(IUUIDGenerator)
        tile_id = generator()
        tile_type = self.request.get('type')
        tile = self.get_tile(tile_type, tile_id)
        data_manager = ITileDataManager(tile)
        data_manager.set({})

        meta_data_manager = self.get_meta_data_manager()
        data = meta_data_manager.get()
        tiles = data.get('tiles', []) or []
        tiles.append({
            'id': tile_id,
            'type': tile_type
            })
        data['tiles'] = tiles
        meta_data_manager.set(data)

    def delete_tile(self):
        meta_data_manager = self.get_meta_data_manager()
        meta_data = meta_data_manager.get()

        idx = int(self.request.get('idx'))
        tiles = meta_data['tiles']
        tile_data = tiles[idx]
        tile_type = tile_data['type']

        tile = self.get_tile(tile_type, tile_data['id'])

        dataManager = ITileDataManager(tile)
        dataManager.delete()

        notify(ObjectRemovedEvent(tile))

        tiles.remove(tile_data)
        meta_data_manager.set(meta_data)

    def change_mode(self):
        meta_data_manager = self.get_meta_data_manager()
        meta_data = meta_data_manager.get()
        meta_data['mode'] = self.request.get('value')
        meta_data_manager.set(meta_data)

    def addTilesData(self, meta_tile):
        tiles = meta_tile.data.get('tiles', [])[:]
        annotations = IAnnotations(meta_tile.context)
        for tile in tiles:
            tile_type = queryUtility(ITileType, name=tile['type'])
            tile['label'] = tile_type.title
            if tile['type'] == 'castle.cms.fragment':
                data = annotations.get(TILE_ANNOTATIONS_KEY_PREFIX + '.' + tile['id'])
                if data and data.get('fragment'):
                    name = data.get('fragment')
                    tile['label'] += ': ' + name.capitalize().replace('-', ' ')
        return tiles

    def info(self):
        portal = api.portal.get()
        _id = self.get_working_copy_meta_id()

        portal_path = '/'.join(portal.getPhysicalPath())
        current_path = '/'.join(self.context.getPhysicalPath())[len(portal_path):] or '/'

        effective_tiles = []
        for effective_tile in meta.getEffectiveTiles(self.context, self.request, _id,
                                                     self.request.form.get('metaId')):
            effective_tiles.append({
                'path': '/'.join(effective_tile.context.getPhysicalPath())[len(portal_path):] or '/',  # noqa
                'data': self.addTilesData(effective_tile)
            })

        tile = meta.getTile(self.context, self.request, _id)
        mode = tile.data.get('mode', 'parent') or 'parent'
        if current_path == '/' and mode == 'parent':
            mode = 'show'
        return json.dumps({
            'current': current_path or '/',
            'current_url': self.context.absolute_url(),
            'mode': mode,
            'effective_tiles': effective_tiles,
            'tiles': self.addTilesData(tile)
        })


class RenderLayout(BrowserView):
    javascript = '''
$("*").each(function () {

  // Local variables
  var obj;

  obj = $(this);

  // Check if block element
  if (obj.css('display') === 'block') {
    // Add blur class
    if(!obj.hasClass('castle-tile-container')){
        obj.addClass('mosaic-blur');
    }
  }
  $('.castle-tile-container').each(function(){
    $(this).parents('.mosaic-blur').removeClass('mosaic-blur');
  });
});
'''
    styles = '''.mosaic-blur {
    opacity: 0.7;
}
.castle-tile-container {
outline: 2px dashed #ccc;
margin: 3px;
text-align: center;
font-weight: bold;
padding: 20px;
cursor: pointer;
z-index: 9999;
position: relative;
}
.castle-tile-container:hover {
outline: 2px dashed orange;
}
'''

    def __call__(self):
        self.request.response.setHeader('X-Theme-Applied', 'true')
        layout = self.request.get('layout')
        transform = theming.getTransform(self.context, self.request)

        layout = transform.get_layout(self.context, layout, request=self.request)
        portal = api.portal.get()
        portal_url = portal.absolute_url()
        context_url = self.context.absolute_url()

        theme_base_url = '%s/++%s++%s/index.html' % (
            portal_url,
            THEME_RESOURCE_NAME,
            transform.name)

        content = {
            'main': '<p>Content from page</p>',
            'left': '',
            'right': ''
        }

        utils = getMultiAdapter((self.context, self.request),
                                name='castle-utils')

        layout = layout(
            portal_url=portal_url,
            site_url=portal_url,
            context_url=context_url,
            request=self.request,
            context=self.context,
            portal=portal,
            site=portal,
            theme_base_url=theme_base_url,
            content=content,
            anonymous=api.user.is_anonymous(),
            debug=api.env.debug_mode(),
            utils=utils,
            raw=True
        )

        dom = getHTMLSerializer([layout])
        transform.rewrite(dom, theme_base_url)

        root = dom.tree.getroot()
        for tile in root.cssselect('[data-tile*="@@castle.cms.meta/"]'):
            slot_id = tile.attrib['data-tile'].split('/@@castle.cms.meta/')[-1]

            title = None
            if '?' in slot_id:
                slot_id, _, qs = slot_id.partition('?')
                query = dict(urllib.parse_qsl(qs))
                title = query.get('title')
            else:
                title = slot_id.replace('meta-', '').capitalize().replace('-', ' ')
            tile.attrib['data-tile-id'] = slot_id
            tile.attrib['data-tile-title'] = title
            tile.attrib['class'] = 'castle-tile-container'
            tile.text = 'Edit %s slot' % title

        overlay = etree.Element('div')
        overlay.attrib['class'] = 'expose-overlay'
        root.cssselect('body')[0].append(overlay)

        javascript = etree.Element('script')
        javascript.text = self.javascript
        root.cssselect('body')[0].append(javascript)

        style = etree.Element('style')
        style.text = self.styles
        root.cssselect('body')[0].append(style)

        transform.dynamic_grid(dom.tree)
        return tostring(dom.tree)
