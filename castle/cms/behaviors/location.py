from castle.cms.widgets import MapPointsFieldWidget
from plone.app.z3cform.widget import AjaxSelectFieldWidget
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from Products.CMFPlone.utils import validate_json
from zope import schema
from zope.interface import alsoProvides


class ILocation(model.Schema):

    model.fieldset(
        'categorization',
        fields=['locations', 'coordinates'],
    )

    form.widget('locations', AjaxSelectFieldWidget,
                vocabulary='castle.cms.vocabularies.Locations')
    locations = schema.List(
        title=u'Locations',
        description=u'Locations to be referred to with this content',
        required=False,
        value_type=schema.TextLine()
    )

    form.widget(coordinates=MapPointsFieldWidget)
    coordinates = schema.Text(
        title=u'Coordinates',
        description=u'Providing coordinates to be able to map this content. '
                    u'You can select more than one set of coordinates',
        default=u'[]',
        constraint=validate_json,
        required=False
    )


alsoProvides(ILocation, IFormFieldProvider)
