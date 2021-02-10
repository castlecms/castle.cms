# -*- coding: utf-8 -*-
from plone.app.contenttypes import _
from plone.app.textfield import RichText as RichTextField
from plone.autoform.interfaces import IFormFieldProvider
from plone.autoform.view import WidgetsView
from plone.autoform import directives as form
from plone.dexterity.interfaces import IDexterityContent
from plone.supermodel import model
from zope.component import adapter
from zope.interface import implementer
from zope.interface import provider
from plone.app.z3cform.widget import RichTextFieldWidget
from zope import schema


@provider(IFormFieldProvider)
class IOverview(model.Schema):

    overview = RichTextField(
        title=_(u'Overview'),
        description=u"Overview for what the content is about. This is longer than "
                    u"the description and allows for rich text",
        required=False,
    )
    form.widget('overview', RichTextFieldWidget)

    form.order_after(change_log='*')
    change_log = schema.Text(
        required=True,
        title=u"Change Log",
        description=u"Detail any changes made to this content item.",
        default=u''
    )


@implementer(IOverview)
@adapter(IDexterityContent)
class Overview(object):

    def __init__(self, context):
        self.context = context


class WidgetView(WidgetsView):
    schema = IOverview
