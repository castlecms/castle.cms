from castle.cms.widgets import SelectFieldWidget
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import alsoProvides
from zope.schema.vocabulary import SimpleVocabulary


class ISearch(model.Schema):

    model.fieldset(
        'settings',
        fields=['searchterm_pins', 'robot_configuration'],
    )

    searchterm_pins = schema.List(
        title=u'Search Term Pins',
        description=u'Searches this content should show top in results for.',
        required=False,
        value_type=schema.TextLine(),
        default=[]
    )

    directives.widget('robot_configuration', SelectFieldWidget)
    robot_configuration = schema.List(
        title=u'How robots should behave with this content',
        description=u'Robot index and consume content on the web. '
                    u'This allows you to remove content from search indexes.',
        required=False,
        defaultFactory=lambda: ['index', 'follow'],
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary([
                SimpleVocabulary.createTerm('index', 'index', 'Index'),
                SimpleVocabulary.createTerm('follow', 'follow', 'Follow links'),
                SimpleVocabulary.createTerm('noimageindex', 'noimageindex', 'Do not index images'),
                SimpleVocabulary.createTerm(
                    'noarchive', 'noarchive',
                    'Search engines should not show a cached link '
                    'to this page on a SERP'),
                SimpleVocabulary.createTerm(
                    'nosnippet', 'nosnippet',
                    'Tells a search engine not to show a snippet of this page '
                    '(i.e. meta description) of this page on a SERP.'),
            ])
        )
    )


alsoProvides(ISearch, IFormFieldProvider)
