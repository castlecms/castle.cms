from plone.app.mosaic.interfaces import IMosaicRegistryAdapter
from Products.CMFPlone.interfaces import ITinyMCESchema
from zope.component import getUtility
from castle.cms.tiles.dynamic import get_tile_manager
from plone.registry.interfaces import IRegistry
from plone.app.mosaic.registry import MosaicRegistry
from plone import api
from zope.interface import implementer
from zope.component import adapter
from castle.cms import cache


MOSAIC_CACHE_DURATION = 1 * 60
_rich_text_widget_types = (
    'plone_app_z3cform_wysiwyg_widget_WysiwygWidget',
    'plone_app_z3cform_wysiwyg_widget_WysiwygFieldWidget',
    'plone_app_widgets_dx_RichTextWidget',
    'plone_app_z3cform_widget_RichTextFieldWidget',
)


@implementer(IMosaicRegistryAdapter)
@adapter(IRegistry)
class CastleMosaicRegistry(MosaicRegistry):
    """
    Overrides mosaic registry adapter
    """
    def parseRegistry(self):
        cache_key = '%s-mosaic-registry' % '/'.join(
            api.portal.get().getPhysicalPath()[1:])
        if not api.env.debug_mode():
            try:
                return cache.get(cache_key)
            except KeyError:
                result = super(CastleMosaicRegistry, self).parseRegistry()
        else:
            result = super(CastleMosaicRegistry, self).parseRegistry()

        mng = get_tile_manager()
        for tile in mng.get_tiles():
            if tile.get('hidden'):
                continue
            key = 'castle_cms_dynamic_{}'.format(tile['id'])
            category = tile.get('category') or 'advanced'
            category_id = category.replace(' ', '_').lower()
            if category_id not in result['plone']['app']['mosaic']['tiles_categories']:
                result['plone']['app']['mosaic']['tiles_categories'][category_id] = {
                    'label': category,
                    'name': category_id,
                    'weight': 100
                }
            result['plone']['app']['mosaic']['app_tiles'][key] = {
                'category': category_id,
                'default_value': None,
                'favorite': False,
                'label': tile['title'],
                'name': tile['name'],
                'tile_type_id': u'castle.cms.dynamic',
                'read_only': False,
                'rich_text': False,
                'settings': True,
                'tile_type': u'app',
                'weight': tile['weight']
            }

        registry = getUtility(IRegistry)
        settings = registry.forInterface(
            ITinyMCESchema, prefix="plone", check=False)
        if settings.libraries_spellchecker_choice != 'AtD':
            cache.set(cache_key, result, MOSAIC_CACHE_DURATION)
            return result

        # add atd config to toolbar dynamically
        mos_settings = result['plone']['app']['mosaic']
        mos_settings['richtext_toolbar']['AtD'] = {
            'category': u'actions',
            'name': u'toolbar-AtD',
            'weight': 0,
            'favorite': False,
            'label': u'After the deadline',
            'action': u'AtD',
            'icon': False
        }
        for widget_type in _rich_text_widget_types:
            mos_settings['widget_actions'][widget_type]['actions'].append('toolbar-AtD')  # noqa
        mos_settings['structure_tiles']['text']['available_actions'].append('toolbar-AtD')  # noqa
        mos_settings['app_tiles']['plone_app_standardtiles_rawhtml']['available_actions'].append('toolbar-AtD')  # noqa
        cache.set(cache_key, result, MOSAIC_CACHE_DURATION)
        return result
