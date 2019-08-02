import json

from castle.cms.behaviors.location import ILocation
from castle.cms.widgets import SelectFieldWidget
from plone import api
from plone.app.z3cform.layout import wrap_form
from plone.dexterity.interfaces import IDexterityItem
from Products.CMFPlone.browser.syndication import adapters
from Products.CMFPlone.browser.syndication import settings
from Products.CMFPlone.browser.syndication import views
from Products.CMFPlone.browser.syndication.views import FeedView
from Products.CMFPlone.interfaces.syndication import IFeedSettings as IBaseFeedSettings
from Products.CMFPlone.interfaces.syndication import ISiteSyndicationSettings
from Products.CMFPlone.interfaces.syndication import ISyndicatable
from Products.Five import BrowserView
from z3c.form import button
from z3c.form import field
from zope import schema
from zope.component import adapts
from zope.component import getUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary


class IFeedSettings(IBaseFeedSettings):
    sort_on = schema.Choice(
        title=u'Sort on',
        default='effective',
        vocabulary=SimpleVocabulary([
            SimpleVocabulary.createTerm('effective', 'effective', 'Publication Date'),
            SimpleVocabulary.createTerm('modified', 'modified', 'Modification Date'),
            SimpleVocabulary.createTerm('start', 'start', 'Start(event)'),
            SimpleVocabulary.createTerm('getObjPositionInParent',
                                        'getObjPositionInParent', 'Position')
        ])
    )

    sort_reverse = schema.Bool(
        title=u'Reverse sort',
        description=u'Order items in reverse order',
        default=True)

    categories = schema.List(
        title=u'ITunes categories',
        description=u'Only for itunes feed',
        value_type=schema.TextLine(),
        default=[],
        required=False,
        missing_value=[]
    )


class FeedSettings(settings.FeedSettings):
    implements(IFeedSettings)
    adapts(ISyndicatable)

    def __getattr__(self, name):
        default = None
        if name in ISiteSyndicationSettings.names():
            default = getattr(self.site_settings, name)
        elif name == 'enabled' and self.site_settings.default_enabled:
            default = True
        elif name in IFeedSettings.names():
            default = IFeedSettings[name].default

        return self._metadata.get(name, default)


class ItemFeedSettings(settings.FeedSettings):
    '''
    Implement basic item feed settings for static values
    of always being disabled. This prevent any errors
    if feed setting data is attempted to be looked against
    a non-folder item
    '''
    implements(IFeedSettings)
    adapts(IDexterityItem)

    enabled = False
    sort_on = 'effective'
    sort_reverse = True
    categories = []
    feed_types = ()
    render_body = False
    max_items = 0


class SettingsForm(views.SettingsForm):

    def update(self):
        if self.context.portal_type in ('Collection', 'Feed'):
            self.fields = field.Fields(IFeedSettings).omit('sort_on', 'sort_reverse')
        else:
            self.fields = field.Fields(IFeedSettings)
        self.fields['feed_types'].widgetFactory = SelectFieldWidget
        super(SettingsForm, self).update()

    @button.buttonAndHandler(u'Cancel', name='cancel')
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(u'Save', name='save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        self.request.response.redirect(self.context.absolute_url())


SettingsFormView = wrap_form(SettingsForm)


class FolderFeed(adapters.FolderFeed):
    def _brains(self):
        catalog = api.portal.get_tool('portal_catalog')
        sort_order = 'ascending'
        if self.settings.sort_reverse or self.settings.sort_reverse is None:
            sort_order = 'reverse'
        return catalog(
            path={
                'query': '/'.join(self.context.getPhysicalPath()),
                'depth': 1
            },
            sort_order=sort_order,
            sort_on=self.settings.sort_on or 'effective',
            sort_limit=self.settings.limit or 15)


class KMLFeedView(FeedView):
    content_type = 'application/vnd.google-earth.kml+xml'

    def get_coordinates(self, item):
        data = ILocation(item.context, None)
        if data is None:
            return

        try:
            data = json.loads(data.coordinates)
            if type(data) == dict:
                data = [data]
            return data
        except Exception:
            pass


class JSONFeedView(FeedView):
    content_type = 'application/json'

    def index(self):
        items = []
        feed = self.feed()
        render_body = feed.settings.render_body

        for item in feed.items:
            json_item = {
                'title': item.title,
                'description': item.description,
                'url': item.link,
                'modified': item.modified.ISO8601(),
                'file_url': item.file_type and item.file_url,
                'file_type': item.file_type,
                'file_length': item.file_length,
                'image_url': item.image_url,
                'uid': feed.uid
            }

            if render_body:
                json_item['body'] = item.render_content_core()
            items.append(json_item)

        return json.dumps({
            'url': feed.link,
            'title': feed.title,
            'description': feed.description,
            'modified': feed.modified.ISO8601(),
            'uid': feed.uid,
            'logo': feed.logo,
            'items': items
        })


class ContentFeedView(BrowserView):

    @property
    def feed_types(self):
        factory = getUtility(IVocabularyFactory,
                             "plone.app.vocabularies.SyndicationFeedTypes")
        vocabulary = factory(self.context)
        types = []
        settings = IBaseFeedSettings(self.context)
        for typ in settings.feed_types:
            types.append(vocabulary.getTerm(typ))
        return types
