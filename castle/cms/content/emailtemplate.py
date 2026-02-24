from castle.cms.widgets import AjaxSelectFieldWidget
from castle.cms.widgets import SelectFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Item
from zope.interface import Interface, implementer
import zope.schema as schema
from plone.supermodel import model
from plone.app.z3cform.widget import RichTextFieldWidget
from plone.app.textfield import RichText as RichTextField


def get_send_to_entities_description(recipient, recipients=None, form_field_title=None):
    if recipients is None:
        recipients = recipient + 's'
    if form_field_title is None:
        form_field_title = 'Send to {}'.format(recipients)
    return (
        u'{capitalized_recipients} that should receive this email. This {recipient} will only receive '
        u'this email if loading this template into a form that includes "{form_field_title}" field.'
    ).format(
        capitalized_recipients=recipients.capitalize(),
        recipient=recipient,
        form_field_title=form_field_title,
    )


class IEmailTemplate(Interface):

    model.fieldset(
        'email_fields',
        label=u'Email Fields',
        fields=[
            'email_subject',
            'send_from',
            'send_to_groups',
            'send_to_users',
            'send_to_subscriber_categories',
            'send_to_custom',
            'email_body',
        ]
    )
    email_subject = schema.TextLine(
        title=u'Email Subject',
        description=u'The Subject Line (RE:) of the email',
        required=False,
    )

    send_from = schema.TextLine(
        title=u'Custom FROM address',
        description=u'The email will have this value as the sender',
        required=False,
    )

    directives.widget(
        'send_to_groups',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Groups',
    )
    send_to_groups = schema.List(
        title=u'Send to groups',
        description=get_send_to_entities_description('user group'),
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Groups'
        ),
        required=False,
    )

    directives.widget(
        'send_to_users',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Users'
    )
    send_to_users = schema.List(
        title=u'Send to users',
        description=get_send_to_entities_description('user'),
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Users',
        ),
        required=False,
    )

    directives.widget('send_to_subscriber_categories', SelectFieldWidget)
    send_to_subscriber_categories = schema.List(
        title=u'Send to subscriber categories',
        description=get_send_to_entities_description('subscriber category', 'subscription categories'),
        required=False,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories',
        ),
    )

    send_to_custom = schema.List(
        title=u'Additional recipients',
        description=(
            get_send_to_entities_description('additional recipient') +
            u' (This textarea can be expanded by dragging the bottom right corner to see more lines at once)'
        ),
        value_type=schema.TextLine(),
        required=False,
    )

    directives.widget('email_body', RichTextFieldWidget)
    email_body = RichTextField(
        title=u'Email Body',
        description=u'The body of the email',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=False,
    )


@implementer(IEmailTemplate)
class EmailTemplate(Item):
    pass
