import json
import logging
import time

from plone import api
from plone.app.theming.interfaces import THEME_RESOURCE_NAME
from plone.app.theming.utils import getCurrentTheme
from plone.app.tiles import MessageFactory as _
from plone.app.tiles.browser import add
from plone.app.tiles.browser import edit
from plone.app.tiles.browser import traversal
from plone.autoform import directives
from plone.memoize import forever
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory
from plone.supermodel import model
from plone.supermodel.model import SchemaClass
from plone.tiles import Tile
from plone.tiles.interfaces import IPersistentTile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zExceptions import NotFound
from zope import schema
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.filerepresentation.interfaces import IRawReadFile
from zope.globalrequest import getRequest
from zope.interface import implements
from zope.schema.vocabulary import SimpleVocabulary


logger = logging.getLogger('castle.cms')


class DynamicTile(Tile):
    implements(IPersistentTile)

    def __call__(self):
        mng = get_tile_manager(self.request)
        template = mng.get_template(self.data['tile_id'])
        site = api.portal.get()
        site_url = site.absolute_url()
        registry = getUtility(IRegistry)
        public_url = registry.get('plone.public_url', None)
        if not public_url:
            public_url = site_url
            if not api.user.is_anonymous():
                site_url = public_url

        utils = getMultiAdapter((self.context, self.request),
                                name='castle-utils')
        boundNames = {
            'context': self.context,
            'request': self.request,
            'view': self,
            'portal_url': site_url,
            'public_url': public_url,
            'site_url': site_url,
            'registry': registry,
            'portal': site,
            'utils': utils,
            'data': self.data
        }
        zpt = template.__of__(self.context)
        return zpt._exec(boundNames, [], {})


class IDynamicTileSchema(model.Schema):

    directives.mode(tile_id='hidden')
    tile_id = schema.TextLine(
        title=u'Selected dynamic tile',
        required=True,
        default=None)


CACHE_KEY = 'castle.cms.tiles.dynamic'


class TileManager(object):

    def __init__(self):
        pass

    def get_tile_directory(self):
        theme = getCurrentTheme()
        if theme:
            directory = queryResourceDirectory(
                THEME_RESOURCE_NAME, theme)
            return directory['tiles']
        else:
            raise NotFound

    def read_file(self, fi):
        if fi.__class__.__name__ == "FilesystemFile":
            data = IRawReadFile(fi).read()
        else:
            data = str(fi.data)
        return data

    def read_tile_config(self, directory):
        data = self.read_file(directory['config.json'])
        try:
            return json.loads(data)
        except Exception:
            logger.info('Could not parse tile config {}: {}'.format(
                directory.__name__, data
            ), exc_info=True)
            raise NotFound

    @forever.memoize
    def get_tile(self, tile_id):
        tiles_directory = self.get_tile_directory()
        tile_folder = tiles_directory[tile_id]
        return self.read_tile_config(tile_folder)

    @forever.memoize
    def get_tile_fields(self, tile_id):
        tiles = {}
        for field in self.get_tile(tile_id)['fields']:
            field = field.copy()
            try:
                factory = _field_type_mapping[field.pop('type', 'text')]
            except KeyError:
                continue
            for name in ('title', 'description'):
                if name in field:
                    field[name] = unicode(field[name])
            for name in list(field.keys())[:]:
                if name not in ('title', 'description', 'required', 'vocabulary',
                                'default', 'name'):
                    del field[name]

            if 'required' not in field:
                field['required'] = True

            try:
                field_name = str(field.pop('name'))
                tiles[field_name] = factory(**field)
            except Exception:
                logger.info('Could not create field on tile {}, with options {}'.format(
                    tile_id, field
                ), exc_info=True)
        return tiles

    @forever.memoize
    def get_schema(self, tile_id):
        return SchemaClass(
            name=tile_id,
            bases=(IDynamicTileSchema,),
            # we're mimicking plone.supermodel here so let's us
            # same module
            __module__='plone.supermodel.generated',
            attrs=self.get_tile_fields(tile_id)
        )

    @forever.memoize
    def get_template(self, tile_id):
        print('load template {}'.format(tile_id))
        tiles_directory = self.get_tile_directory()
        tile_folder = tiles_directory[tile_id]
        fi = tile_folder['template.html']
        if fi.__class__.__name__ == "FilesystemFile":
            data = IRawReadFile(fi).read()
        else:
            data = str(fi.data)
        return ZopePageTemplate(tile_id, text=data)

    @forever.memoize
    def get_tiles(self):
        try:
            tiles_directory = self.get_tile_directory()
        except NotFound:
            return []
        tiles = []
        for tile_id in tiles_directory.listDirectory():
            directory = tiles_directory[tile_id]
            try:
                config = self.read_tile_config(directory)
            except NotFound:
                continue
            tiles.append({
                'id': tile_id,
                'category': config.get('category', 'app'),
                'title': config.get('title', 'Tile'),
                'description': config.get('description', ''),
                'name': tile_id,
                'weight': config.get('weight', 200)
            })
        return tiles


_cache = {}


def get_tile_manager(request=None):
    if request is None:
        request = getRequest()
    cache_key = '{}.manager'.format(CACHE_KEY)
    if cache_key not in request.environ:
        if api.env.debug_mode():
            request.environ[cache_key] = TileManager()
        else:
            # check for value in cache
            theme = getCurrentTheme()
            item_cache_key = '{}.manager.{}'.format(CACHE_KEY, theme)
            if item_cache_key not in _cache:
                _cache[item_cache_key] = {
                    'when': time.time(),
                    'value': TileManager()
                }
            else:
                registry = queryUtility(IRegistry)
                theme_cache_time = getattr(registry, '_theme_cache_mtime', 0)
                if theme_cache_time > _cache[item_cache_key]['when']:
                    _cache[item_cache_key] = {
                        'when': time.time(),
                        'value': TileManager()
                    }
            request.environ[cache_key] = _cache[item_cache_key]['value']
    return request.environ[cache_key]


def ChoiceFactory(**options):
    if 'vocabulary' not in options:
        options['vocabulary'] = SimpleVocabulary.fromValues([])
    else:
        options['vocabulary'] = SimpleVocabulary.fromValues(options['vocabulary'])
    return schema.Choice(**options)


def ArrayFactory(**options):
    if 'value_type' not in options:
        options['value_type'] = schema.TextLine()
    return schema.List(**options)


def ObjectFactory(**options):
    if 'value_type' not in options:
        options['value_type'] = schema.TextLine()
    if 'key_type' not in options:
        options['key_type'] = schema.TextLine()
    return schema.Dict(**options)


_field_type_mapping = {
    'text': schema.TextLine,
    'int': schema.Int,
    'float': schema.Float,
    'decimal': schema.Decimal,
    'datetime': schema.Datetime,
    'date': schema.Date,
    'timedelta': schema.Timedelta,
    'time': schema.Time,
    'password': schema.Password,
    'boolean': schema.Bool,
    'choice': ChoiceFactory,
    'uri': schema.URI,
    'dottedname': schema.DottedName,
    'array': ArrayFactory,
}


class AddForm(add.DefaultAddForm):

    @property
    def schema(self):
        mng = get_tile_manager(self.request)
        return mng.get_schema(self.tile_id)

    @property
    def label(self):
        mng = get_tile_manager(self.request)
        tile = mng.get_tile(self.tile_id)
        return 'Add ' + tile.get('title', 'Tile')

    @property
    def description(self):
        mng = get_tile_manager(self.request)
        tile = mng.get_tile(self.tile_id)
        return tile.get('description', '')

    def update(self):
        super(AddForm, self).update()
        if not self.widgets['tile_id'].value:
            self.widgets['tile_id'].value = unicode(
                self.widgets['tile_id'].extract() or self.tile_id)


class AddView(add.DefaultAddView):
    form = AddForm

    def __init__(self, context, request, tileType):
        super(AddView, self).__init__(context, request, tileType)
        self.form_instance.tile_id = unicode(self.request.get(
            'castle.cms.dynamic.tile_id', ''))
        # weird bug where it isn't passing in as unicode?
        self.request['castle.cms.dynamic.tile_id'] = self.form_instance.tile_id


class AddTileTraversal(traversal.AddTile):
    def __call__(self):
        self.errors = {}
        self.request['disable_border'] = True
        if 'form.button.Create' in self.request:
            newTileType = self.request.get('tiletype', None)
            if newTileType is None:
                self.errors['tiletype'] = _(u"You must select the type of " +
                                            u"tile to create")

            if len(self.errors) == 0:
                extra = ''
                if newTileType == 'castle.cms.dynamic':
                    extra = '?castle.cms.dynamic.tile_id={}'.format(
                        self.request.get('tile_id', ''))
                self.request.response.redirect("%s/@@add-tile/%s%s" % (
                    self.context.absolute_url(), newTileType, extra))
                return ''

        return self.index()


class EditForm(edit.DefaultEditForm):

    @property
    def label(self):
        mng = get_tile_manager(self.request)
        tile = mng.get_tile(self.tile_id)
        return 'Edit ' + tile.get('title', 'Tile')

    @property
    def description(self):
        mng = get_tile_manager(self.request)
        tile = mng.get_tile(self.tile_id)
        return tile.get('description', '')

    @property
    def schema(self):
        mng = get_tile_manager(self.request)
        data = self.getContent()
        return mng.get_schema(data['tile_id'])


class EditView(edit.DefaultEditView):
    form = EditForm
