from castle.cms import  _
from plone.supermodel import model
from zope import schema
from plone.app.textfield import RichText
from plone.autoform import directives
# from castle.cms.widgets import (AjaxSelectFieldWidget, SelectFieldWidget,
#                                 TinyMCETextFieldWidget)

class IEmailTemplateSchema(model.Schema):

    """An email template."""

    subject = schema.ASCIILine(
        title=u'Subject',
        required=False,
    )

    send_from = schema.TextLine(
        title=u'Custom FROM address',
        required=False,
    )

    # directives.widget(
    #     'send_to_groups',
    #     AjaxSelectFieldWidget,
    #     vocabulary='plone.app.vocabularies.Groups',
    #     required = False
    # )

    send_to_groups = schema.List(
        title=u'Send to groups',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Groups'
        ),
        required=False
    )

    # directives.widget(
    #     'send_to_users',
    #     AjaxSelectFieldWidget,
    #     vocabulary='plone.app.vocabularies.Users',
    #     required = False
    # )

    send_to_users = schema.List(
        title=u'Send to users',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Users'
        ),
        required=False
    )

    send_to_custom = schema.List(
        title=u'To(additional)',
        description=u'Additional email addresses, one per line, to '
                    u'send emails to.',
        value_type=schema.TextLine(),
        required=False
    )

    body = RichText(
        title=u'Body',
        description=u'Message body',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=False
    )




    # subject = schema.ASCIILine(
    #     title = _(u'Email Template Subject'),
    #     description = _(u'The subject line for the email'),
    #     required = True,
    # )
    # title = schema.ASCIILine(
    #     title = _(u'Email Template Subject'),
    #     description = _(u'The subject line for the email'),
    #     required = True,
    # )

    # body = RichText(
    #     title=u'Body',
    #     description=u'Message body',
    #     default_mime_type='text/html',
    #     output_mime_type='text/html',
    #     allowed_mime_types=('text/html',),
    #     required=True
    # )

    # send_from = schema.TextLine(
    #     title = _(u'Email "From:" Address'),
    #     description = _(u'The sender\'s name for this email'),
    #     required = False,
    # )

    # send_to_groups = schema.List(
    #     title=u'Send to groups',
    #     value_type=schema.Choice(
    #         vocabulary='plone.app.vocabularies.Groups'
    #     ),
    #     required=False
    # )

    # send_to_users = schema.List(
    #     title=u'Send to users',
    #     value_type=schema.Choice(
    #         vocabulary='plone.app.vocabularies.Users'
    #     ),
    #     required=False
    # )

    # send_to_custom = schema.List(
    #     title=u'To(additional)',
    #     description=u'Additional email addresses, one per line, to '
    #                 u'send emails to.',
    #     value_type=schema.TextLine(),
    #     required=False
    # )

# @interface.implementer(IEmailTemplate)
# class EmailTemplate(object):
#     def __init__(self, **kwargs):
#         for key, value in kwargs.items():
#             self[key] = value
#     def __repr__(self):
#         return "<Template with name=%r, body=%r>" % (self.name, self.body)