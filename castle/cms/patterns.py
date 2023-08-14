import json

from Acquisition import aq_inner, aq_parent
from borg.localrole.interfaces import IFactoryTempFolder
from castle.cms import cache, theming
from castle.cms.interfaces import IDashboard
from castle.cms.utils import get_upload_fields
from plone import api
from plone.app.imaging.utils import getAllowedSizes
from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.dexterity.interfaces import IDexterityContainer
from plone.memoize.view import memoize
from plone.registry.interfaces import IRegistry
from plone.tiles.interfaces import ITileType
from plone.uuid.interfaces import IUUID
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.interfaces._content import IFolderish
from Products.CMFPlone.interfaces import IPatternsSettings, IPloneSiteRoot

# Plone5.2 - 'PloneSettingsAdapter' name and location changed
from Products.CMFPlone.patterns.settings import PatternSettingsAdapter
from Products.CMFPlone.patterns.tinymce import TinyMCESettingsGenerator
from zope.component import getUtility
from zope.interface import implements
from castle.cms.services.google import youtube

from zope.schema.interfaces import IVocabularyFactory
from Products.CMFPlone.interfaces import ILinkSchema
from Products.CMFPlone.interfaces import IPatternsSettings
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.patterns.tinymce import TinyMCESettingsGenerator
from Products.CMFPlone.utils import get_portal
from plone.app.z3cform.utils import call_callables
from zope.component import getUtility
from zope.i18n import translate
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from plone.app.widgets.utils import get_relateditems_options
from plone.app.content.browser.interfaces import IFolderContentsView


class CastleTinyMCESettingsGenerator(TinyMCESettingsGenerator):

    def get_tiny_config(self):
        config = super(CastleTinyMCESettingsGenerator, self).get_tiny_config()
        if 'paste' not in config['plugins']:
            config['plugins'] += 'paste'
        config['paste_data_images'] = True
        config['paste_as_text'] = True
        config['paste_word_valid_elements'] = "b,strong,i,em,h1,h2,h3,h4,ul,li"
        config['paste_retain_style_properties'] = ''
        config['paste_merge_formats'] = True
        content_css = config['content_css'].split(',')
        style_css = config['importcss_file_filter'].split(',')
        content_css.extend(style_css)
        config['content_css'] = ','.join(set(content_css))
        config['browser_spellcheck'] = True
        formats = config.get('formats')
        if isinstance(formats, list):
            config['style_formats'].extend(formats)
        return config

# Plone5.2 - Migrated new 'PatternSettingsAdapter' here to get tinyMCE to initialize
@implementer(IPatternsSettings)
class CastleSettingsAdapter(PatternSettingsAdapter):
    """
    Provides default plone settings relevant for patterns.
    """

    def __init__(self, context, request, field):
        self.request = request
        self.context = context
        self.field = field

    def __call__(self):
        data = super(CastleSettingsAdapter, self).__call__()
        data.update(self.mark_special_links())
        data.update(self.structure_updater())
        return data

    def structure_updater(self):
        """Generate the options for the structure updater pattern.
        If we're not in folder contents view, do not expose these options.
        """
        data = {}
        view = self.request.get('PUBLISHED', None)
        if IFolderContentsView.providedBy(view):
            data = {
                'data-pat-structureupdater': json.dumps({
                    'titleSelector': '.documentFirstHeading',
                    'descriptionSelector': '.documentDescription'
                })
            }
        return data

    def mark_special_links(self):
        result = {}

        registry = getUtility(IRegistry)
        settings = registry.forInterface(
            ILinkSchema, prefix="plone", check=False)

        msl = settings.mark_special_links
        elonw = settings.external_links_open_new_window
        if msl or elonw:
            result = {
                'data-pat-markspeciallinks': json.dumps(
                    {
                        'external_links_open_new_window': elonw,
                        'mark_special_links': msl
                    }
                )
            }
        return result

    @property
    def image_scales(self):
        factory = getUtility(
            IVocabularyFactory,
            'plone.app.vocabularies.ImagesScales'
        )
        vocabulary = factory(self.context)
        ret = [{
            'title': translate(it.title), 'value': it.value}
            for it in vocabulary]
        ret = sorted(ret, key=lambda it: it['title'])
        return json.dumps(ret)

    def tinymce(self):
        """
        data-pat-tinymce : JSON.stringify({
            relatedItems: {
              vocabularyUrl: config.portal_url +
                '/@@getVocabulary?name=plone.app.vocabularies.Catalog'
            },
            tiny: config,
            prependToUrl: 'resolveuid/',
            linkAttribute: 'UID',
            prependToScalePart: '/@@images/image/'
          })
        """
        generator = CastleTinyMCESettingsGenerator(self.context, self.request)
        settings = generator.settings
        folder = aq_inner(self.context)

        # Test if we are currently creating an Archetype object
        if IFactoryTempFolder.providedBy(aq_parent(folder)):
            folder = aq_parent(aq_parent(aq_parent(folder)))
        if not IFolderish.providedBy(folder):
            folder = aq_parent(folder)

        if IPloneSiteRoot.providedBy(folder):
            initial = None
        else:
            initial = IUUID(folder, None)

        portal = get_portal()
        portal_url = portal.absolute_url()
        current_path = folder.absolute_url()[len(portal_url):]

        image_types = settings.image_objects or []

        server_url = self.request.get('SERVER_URL', '')
        site_path = portal_url[len(server_url):]

        related_items_config = get_relateditems_options(
            context=self.context,
            value=None,
            separator=';',
            vocabulary_name='plone.app.vocabularies.Catalog',
            vocabulary_view='@@getVocabulary',
            field_name=None
        )
        related_items_config = call_callables(
            related_items_config,
            self.context
        )

        configuration = {
            'base_url': self.context.absolute_url(),
            'imageTypes': image_types,
            'imageScales': self.image_scales,
            'linkAttribute': 'UID',
            # This is for loading the languages on tinymce
            'loadingBaseUrl': '{0}/++plone++static/components/tinymce-builded/'
                              'js/tinymce'.format(portal_url),
            'relatedItems': related_items_config,
            'prependToScalePart': '/@@images/image/',
            'prependToUrl': '{0}/resolveuid/'.format(site_path.rstrip('/')),
            'tiny': generator.get_tiny_config(),
            'upload': {
                'baseUrl': portal_url,
                'currentPath': current_path,
                'initialFolder': initial,
                'maxFiles': 1,
                'relativePath': '@@fileUpload',
                'showTitle': False,
                'uploadMultiple': False,
            },
        }
        return {'data-pat-tinymce': json.dumps(configuration)}
