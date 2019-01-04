from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.resources.browser.cook import cookWhenChangingSettings
from zope.component import getUtility

PROFILE_ID = 'profile-castle.cms:2_2_0'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile('profile-Products.PloneKeywordManager:default')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    cookWhenChangingSettings(api.portal.get())

    # upgrade upload fields
    registry = getUtility(IRegistry)

    if not registry.get('castle.file_upload_fields', None):
        # can be None or [] so we don't do an `is None` check here
        required_upload_fields = registry.get(
            'castle.required_file_upload_fields', []) or []
        registry['castle.file_upload_fields'] = [{
            u'name': u'title',
            u'label': u'Title',
            u'widget': u'text',
            u'required': unicode('title' in required_upload_fields).lower(),
            u'for-file-types': u'*'
        }, {
            u'name': u'description',
            u'label': u'Summary',
            u'widget': u'textarea',
            u'required': unicode('description' in required_upload_fields).lower(),
            u'for-file-types': u'*'
        }, {
            u'name': u'tags',
            u'label': u'Tags',
            u'widget': u'tags',
            u'required': unicode('tags' in required_upload_fields).lower(),
            u'for-file-types': u'*'
        }, {
            u'name': u'youtube_url',
            u'label': u'Youtube URL',
            u'widget': u'text',
            u'required': unicode('youtube_url' in required_upload_fields).lower(),
            u'for-file-types': u'video'
        }]
        if 'castle.required_file_upload_fields' in registry.records._fields:
            del registry.records['castle.required_file_upload_fields']
