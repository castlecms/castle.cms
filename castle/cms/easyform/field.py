import ast
from plone.uuid.interfaces import IUUID

from castle.cms.utils import parse_query_from_data
from castle.cms.widgets import QueryFieldWidget
from plone.autoform import directives as form
from plone.schemaeditor.fields import FieldFactory
from plone.schemaeditor.fields import TextLineChoiceField
from plone.schemaeditor.interfaces import IFieldEditFormSchema
from Products.CMFCore.utils import getToolByName
from zope import schema
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.i18nmessageid import MessageFactory
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.schema.interfaces import IChoice
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.interfaces import IField
from zope.schema.vocabulary import SimpleVocabulary


_ = MessageFactory('castle.cms')


class IQueryChoice(IChoice):
    query = schema.List(
        title=u'Query',
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False
    )

    sort_on = schema.TextLine(
        title=u'Sort on',
        required=False,
        default=u'effective'
    )

    sort_reversed = schema.Bool(
        title=u'Reversed order',
        required=False,
        default=True
    )

    limit = schema.Int(
        title=u'Limit',
        required=False,
        default=15,
        min=1,
    )


@implementer(IQueryChoice)
class QueryChoice(schema.Choice):

    def __init__(self, query=None, sort_on='effective', sort_reversed=True,
                 limit=15, **kw):
        self.query = query or []
        self.sort_on = sort_on
        self.sort_reversed = sort_reversed
        self.limit = limit
        kw['source'] = QueryChoiceSource(self)  # bind to field
        self._fix_query()
        super(QueryChoice, self).__init__(**kw)

    def _fix_query(self):
        # does not save data properly often here
        for item in (self.query or []):
            if (item['v'] and
                    isinstance(item['v'], basestring) and
                    item['v'][0] in ('[', '{') and
                    item['v'][-1] in (']', '}')):
                item['v'] = ast.literal_eval(item['v'])


@implementer(IContextSourceBinder)
class QueryChoiceSource(object):
    __name__ = 'QueryChoiceSource'

    def __init__(self, field):
        self.field = field

    def get_cache_key(self, context):
        return 'easyform-source-value--{}-{}'.format(
            IUUID(context, 'default'), self.field.__name__)

    def __call__(self, context):
        cache_key = self.get_cache_key(context)
        request = getRequest()
        if request is not None and cache_key in request.environ:
            # prevent doing query many times
            return request.environ[cache_key]

        if not self.field.query:
            return SimpleVocabulary([])

        query = parse_query_from_data({
            'query': self.field.query,
            'sort_on': self.field.sort_on,
            'sort_reversed': self.field.sort_reversed,
        })
        catalog = getToolByName(context, 'portal_catalog')
        if query.get('sort_on', '') not in catalog._catalog.indexes:
            query['sort_on'] = 'effective'

        terms = []
        for item in catalog(**query)[:self.field.limit]:
            terms.append(
                SimpleVocabulary.createTerm(item.id, item.id, item.Title))

        value = SimpleVocabulary(terms)
        if request is not None:
            request.environ[cache_key] = value
        return value


# so we can still resolve correctly
alsoProvides(QueryChoiceSource, IContextSourceBinder)


QueryChoiceFactory = FieldFactory(
    QueryChoice, _(u'label_query_choice_field', default=u'Query Choice'),
    source=QueryChoiceSource)


class IQueryChoiceFieldSchema(IField):
    form.widget(query=QueryFieldWidget)
    query = schema.List(
        title=u'Query',
        value_type=schema.Dict(value_type=schema.Field(),
                               key_type=schema.TextLine()),
        required=False
    )

    sort_on = schema.TextLine(
        title=u'Sort on',
        required=False,
        default=u'effective'
    )

    sort_reversed = schema.Bool(
        title=u'Reversed order',
        required=False,
        default=True
    )

    limit = schema.Int(
        title=u'Limit',
        required=False,
        default=15,
        min=1,
    )


@implementer(IFieldEditFormSchema)
@adapter(IQueryChoice)
def getQueryChoiceFieldSchema(field):
    return IQueryChoiceFieldSchema


@implementer(IQueryChoiceFieldSchema)
@adapter(IQueryChoice)
class TextLineQueryChoiceField(TextLineChoiceField):
    pass
