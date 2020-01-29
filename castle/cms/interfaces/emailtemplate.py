from plone.app.textfield import RichText, RichTextValue
from plone.autoform import directives
from plone.supermodel import model
from zope import schema
from plone.app.z3cform.widget import AjaxSelectFieldWidget, SelectFieldWidget

from plone.autoform.interfaces import IFormFieldProvider

from zope.interface import provider

@provider(IFormFieldProvider)
class IEmailTemplateSchema(model.Schema):

    subject = schema.ASCIILine(
        title=u'Subject',
        required=True,
    )


    send_from = schema.TextLine(
        title=u'Custom FROM address',
        required=False,
    )


    # directives.widget(
    #     'send_to_groups',
    #     SelectFieldWidget,
    #     vocabulary='plone.app.vocabularies.Groups',
    #     required=False
    # )


    # send_to_groups = schema.List(
    #     title=u'Send to groups',
    #     value_type=schema.Choice(
    #         vocabulary='plone.app.vocabularies.Groups'
    #     ),
    #     required=False
    # )


    # directives.widget(send_to_users=SelectFieldWidget)
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


    # directives.widget(send_to_categories=SelectFieldWidget)
    # send_to_categories = schema.List(
    #     title=u'Send to categories',
    #     required=False,
    #     value_type=schema.Choice(
    #         vocabulary='castle.cms.vocabularies.EmailCategories'
    #     )
    # )



    body = RichText(
        title=u'Body',
        description=u'Message body',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=True
    )

 

    
    unsubscribe_links = RichText(
        title=u'Unsubscribe',
        description=u'Email Footer Unsubscribe Links',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=False,
        default=RichTextValue(
            u'<p></p><p></p>'
            u'<p><a href="{{change_url}}">Change your subscription settings</a></p>'
            u'<p><a href="{{unsubscribe_url}}">Unsubscribe from these messages</a></p>',
            'text/html', 'text/html'
        )
    )


    # directives.mode(select_email_template='hidden')
    # directives.widget(select_email_template=SelectFieldWidget)
    # select_email_template = schema.Choice(
    #     title=u'Load Email Template',     
    #     vocabulary='castle.cms.vocabularies.EmailTemplates', 
    #     required=False,
    #     default='None'
    # )