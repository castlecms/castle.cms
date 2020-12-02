from castle.cms.widgets import SelectFieldWidget
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import alsoProvides


class ISearch(model.Schema):

    model.fieldset(
        'settings',
        fields=[
            'searchterm_pins',
            'robot_configuration',
            'backend_robot_configuration',
            'exclude_from_search',
        ],
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
        title=u'How robots should behave with this content on frontend urls',
        description=u'Robots index and consume content on the web. '
                    u'This allows you to remove content from search indexes.',
        required=False,
        defaultFactory=lambda: ['index', 'follow'],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.RobotBehaviors',
        ),
    )

    directives.widget('backend_robot_configuration', SelectFieldWidget)
    backend_robot_configuration = schema.List(
        title=u'How robots should behave with this content on backend urls',
        description=u'Robots index and consume content on the web. '
                    u'This allows you to remove content from search indexes.',
        required=False,
        defaultFactory=lambda: [],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.RobotBehaviors',
        )
    )

    exclude_from_search = schema.Bool(
        title=u'Exclude from searches',
        description=u'If selected, this item will not appear in searches',
        required=True,
        default=False
    )


alsoProvides(ISearch, IFormFieldProvider)
