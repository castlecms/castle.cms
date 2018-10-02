import logging

from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFPlone.interfaces import IPloneSiteRoot
from castle.cms.interfaces import IGlobalTile
from castle.cms.interfaces import IMetaTile
from plone.supermodel import model
from plone.tiles import Tile
from zope import schema
from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.interface import implements
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


logger = logging.getLogger('castle.cms')


class MetaTile(Tile):
    implements(IGlobalTile)

    _template = """<section class="meta-tile-container"
                        id="meta-tile-%(id)s" aria-label="%(id)s">%(content)s</section>"""
    _tile_template = """<div class="tile-container
                                    tile-container-%(type)s
                                    tile-container-index-%(idx)i"
                             id="tile-%(id)s">%(content)s</div>"""

    def render_meta_tile(self, meta_tile, idx_start=0):
        if not meta_tile:
            return ''
        if meta_tile.data.get('mode') == 'hide':
            return ''
        tiles = meta_tile.data.get('tiles') or []
        rendered = ''
        for idx, tile_config in enumerate(tiles):
            tile = getMultiAdapter((self.context, self.request),
                                   name=tile_config['type'])
            alsoProvides(tile, IMetaTile)
            tile.id = tile_config['id']
            tile.__name__ = tile_config['type']
            tile.data_context = meta_tile.context
            tile.wrap = False
            result = tile()
            if result:
                result = result.replace(
                    '<html><body>', '').replace('</body></html>', '').strip()
                if result:
                    rendered += self._tile_template % {
                        'id': tile.id,
                        'content': result,
                        'type': tile.__name__.replace('.', '-'),
                        'idx': idx
                    }
        return rendered

    def index(self):
        meta_tiles = getEffectiveTiles(self.context, self.request, self.id)
        result = ''
        for meta_tile in meta_tiles:
            result += self.render_meta_tile(meta_tile)

        if result:
            result = self._template % {
                'id': self.id,
                'content': result
            }
        return result

    def __call__(self):
        try:
            return self.index()
        except Exception:
            logger.warn('Error rendering meta tile', exc_info=True)
            return ''


class IMetaTileSchema(model.Schema):

    # dict structure:
    #   id: < generated id of file >
    #   type type: < type of tile >
    tiles = schema.List(
        title=u'Tiles',
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False,
        default=[],
        missing_value=[]
    )

    mode = schema.Choice(
        title=u"Mode",
        vocabulary=SimpleVocabulary([
            SimpleTerm('hide', 'hide', u'Hide'),
            SimpleTerm('parent', 'parent', u'Use parent settings'),
            SimpleTerm('show', 'show', u'Show(hides parent tiles)'),
            SimpleTerm('add', 'add', u'Add')
        ]),
        default='parent'
    )


def getEffectiveTiles(ob, req, _id, parent_id=None):
    if parent_id is None:
        parent_id = _id
    tile = getTile(ob, req, _id)
    try:
        data = tile.data
    except TypeError:
        return []
    tiles = []
    mode = data.get('mode') or 'parent'
    while not IPloneSiteRoot.providedBy(ob):
        if mode != 'parent' and mode != 'add':
            break
        if mode == 'add':
            tiles.append(tile)
        ob = aq_parent(ob)
        tile = getTile(ob, req, parent_id)
        mode = tile.data.get('mode') or 'parent'
    tiles.append(tile)
    return list(reversed(tiles))


def getTile(ob, req, _id):
    tile = MetaTile(aq_inner(ob), req)
    alsoProvides(tile, IGlobalTile)
    tile.id = _id
    tile.__name__ = 'castle.cms.meta'
    return tile
