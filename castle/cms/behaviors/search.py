# from plone.app.z3cform.widget import AjaxSelectFieldWidget
# from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import alsoProvides


class ISearch(model.Schema):

    model.fieldset(
        'settings',
        fields=['searchterm_pins'],
    )

    searchterm_pins = schema.List(
        title=u'Search Term Pins',
        description=u'Searches this content should show top in results for.',
        required=False,
        value_type=schema.TextLine(),
        default=[]
    )

    # form.widget(
    #     'searchterm_pins',
    #     AjaxSelectFieldWidget
    # )


alsoProvides(ISearch, IFormFieldProvider)
