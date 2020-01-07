from castle.cms import _
from castle.cms.widgets import (AjaxSelectFieldWidget, SelectFieldWidget)
from plone.app.textfield import RichText
from plone.autoform import directives
from plone.supermodel import model
from zope import schema
from zope.interface import Interface, provider
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from plone.api import portal

@provider(IContextSourceBinder)
def email_template_titles(context):
    catalog = portal.get_tool('portal_catalog')
    email_template_choice_names = [ SimpleVocabulary.createTerm('None')]
    for template_brain in catalog(
        {'portal_type': 'EmailTemplate'}
    ):
        email_template_choice_names.append(
            SimpleVocabulary.createTerm(
                template_brain.getObject().id
            )
        )
    return SimpleVocabulary(email_template_choice_names)


class IEmailTemplateSchema(model.Schema):
    subject = schema.ASCIILine(
        title=_(u'Subject'),
        required=True,
    )

    send_from = schema.TextLine(
        title=u'Custom FROM address',
        required=False,
    )

    directives.widget(
        'send_to_groups',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Groups',
        required = False
    )

    send_to_groups = schema.List(
        title=u'Send to groups',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Groups'
        ),
        required=False
    )

    directives.widget(
        'send_to_users',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Users',
        required = False
    )

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
        required=True
    )

 


    directives.mode(select_email_template='hidden')

    directives.widget(
        'select_email_template',
        SelectFieldWidget,
        source=email_template_titles,
        required = False
    )
    
    select_email_template = schema.List(
        title=u'Load Email Template',
        value_type=schema.Choice(
            source=email_template_titles, 
        ),
        required=False,
    )



    directives.mode(send_to_categories='hidden')
    directives.widget('send_to_categories', SelectFieldWidget)
    send_to_categories = schema.List(
        title=u'Send to categories',
        required=False,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )

    
    directives.mode(select_email_template='hidden')

    select_email_template = schema.Choice(
        title=u'Load Email Template',     
        source=email_template_titles, 
        required=False,
        default='None'
    )