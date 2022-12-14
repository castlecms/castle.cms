from castle.cms import utils
from collective.documentviewer.settings import GlobalSettings as DVGlobalSettings
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.CMFPlone.interfaces.syndication import ISiteSyndicationSettings
from zope.component import getUtility


INDEXES = {
    "contentType": "KeywordIndex",
    "location": "KeywordIndex",
    "hasImage": "BooleanIndex",
    "trashed": "BooleanIndex",
    "has_private_parents": "BooleanIndex",
    "self_or_child_has_title_description_and_image": "BooleanIndex"
}

REMOVE_INDEXES = [
    'in_reply_to',
    'sync_uid',
    'total_comments',
    'cmf_uid',
    'commentators',
    'is_default_page'
]

METADATA = [
    'hasImage',
    'contentType',
    'recurrence',
    'last_modified_by',
    'image_info',
    'navigation_label',
    'has_private_parents',
    'self_or_child_has_title_description_and_image'
]

REMOVE_METADATA = [
    'cmf_uid',
    'commentators',
    'in_response_to',
    'last_comment_date',
    'sync_uid',
    'total_comments',
    'listCreators'
]


def _removeTinyMCEActions(data):
    for name in ('undo', 'redo', 'bold', 'italic'):
        if 'toolbar-' + name in data:
            data.remove('toolbar-' + name)


def castle(context):
    if not context.readDataFile('castle.cms.install.txt'):
        return
    site = context.getSite()

    # create feed folder
    folder = utils.recursive_create_path(site, '/feeds')
    try:
        if api.content.get_state(obj=folder) != 'published':
            api.content.transition(obj=folder, transition='publish')
    except WorkflowException:
        pass

    type_ = 'Collection'
    aspect = ISelectableConstrainTypes(folder, None)

    if (aspect and (
            aspect.getConstrainTypesMode() != 1 or
            [type_] != aspect.getImmediatelyAddableTypes())):
        aspect.setConstrainTypesMode(1)
        aspect.setImmediatelyAddableTypes([type_])
    if not getattr(folder, 'exclude_from_nav', False):
        folder.exclude_from_nav = True
        folder.reindexObject()

    if 'front-page' not in site:
        api.content.create(type='Document', id='front-page', container=site)
        site.setDefaultPage('front-page')

    front_page = site['front-page']

    front_page.title = u'Welcome to CastleCMS'
    front_page.description = u'Welcome to your new CastleCMS site.'

    # enable syndication by default and modify some of the settings
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ISiteSyndicationSettings)
    settings.allowed = True
    settings.default_enabled = False
    settings.show_author_info = False
    settings.search_rss_enabled = False

    utils.add_indexes(INDEXES)
    utils.delete_indexes(REMOVE_INDEXES)
    utils.add_metadata(METADATA)
    utils.delete_metadata(REMOVE_METADATA)

    # add some better defaults for documentviewer
    settings = DVGlobalSettings(site)
    settings.auto_layout_file_types = [
        'pdf', 'word', 'excel', 'ppt', 'rft', 'ps', 'photoshop', 'visio', 'palm']

    # delete some records for mosaic tinymce toolbar
    for action_type in ('plone_app_z3cform_wysiwyg_widget_WysiwygWidget',
                        'plone_app_z3cform_wysiwyg_widget_WysiwygFieldWidget',
                        'plone_app_widgets_dx_RichTextWidget',
                        'plone_app_z3cform_widget_RichTextFieldWidget'):
        try:
            data = registry['plone.app.mosaic.widget_actions.%s.actions' % action_type]
            _removeTinyMCEActions(data)
            registry['plone.app.mosaic.widget_actions.%s.actions' % action_type] = data
        except KeyError:
            pass

    for key in ('plone.app.mosaic.structure_tiles.text.available_actions',
                'plone.app.mosaic.app_tiles.plone_app_standardtiles_rawhtml.available_actions'):
        try:
            data = registry[key]
            _removeTinyMCEActions(data)
            registry[key] = data
        except KeyError:
            pass

    # password reset timeout interval...
    portal_password_reset = api.portal.get_tool('portal_password_reset')
    portal_password_reset.setExpirationTimeout(6)

    # update default session duration
    site.acl_users.session.timeout = 1 * 60 * 15  # 15 min
    site.acl_users.session.refresh_interval = 5 * 60  # 5 minutes
