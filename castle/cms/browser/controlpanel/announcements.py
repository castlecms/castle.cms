from Acquisition import aq_inner
from castle.cms import texting
from castle.cms.browser.utils import Utils
from castle.cms.constants import ALL_SUBSCRIBERS
from castle.cms.interfaces import IAnnoucementData
from castle.cms.tasks import send_email
from castle.cms.tasks import send_email_to_subscribers
from castle.cms.widgets import AjaxSelectFieldWidget
from castle.cms.widgets import SelectFieldWidget
from castle.cms.widgets import TinyMCETextFieldWidget
from plone import api
from plone.app.registry.browser import controlpanel
from plone.app.textfield import RichText
from plone.app.textfield.value import RichTextValue
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button
from z3c.form import form
from zope import schema
from zope.component import getAdapters
from zope.component import getUtility


class AnnouncementsControlPanelForm(controlpanel.RegistryEditForm):
    schema = IAnnoucementData
    schema_prefix = 'castle'
    id = "AnnouncementsControlPanel"
    label = u"Announcements"
    description = ""

    def updateFields(self):
        super(AnnouncementsControlPanelForm, self).updateFields()
        self.fields['site_announcement'].widgetFactory = TinyMCETextFieldWidget


class ISendEmailUsersForm(model.Schema):
    subject = schema.ASCIILine(
        title=u'Subject')

    directives.widget(
        'send_to_groups',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Groups'
    )
    send_to_groups = schema.List(
        title=u'Send to groups',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Groups'
        )
    )

    directives.widget(
        'send_to_users',
        AjaxSelectFieldWidget,
        vocabulary='plone.app.vocabularies.Users'
    )
    send_to_users = schema.List(
        title=u'Send to users',
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.Users'
        ))

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
        required=True)


class SendEmailUsersForm(AutoExtensibleForm, form.Form):
    schema = ISendEmailUsersForm

    ignoreContext = True

    @button.buttonAndHandler(u'Send', name='send')
    def handle_send(self, action):
        data, errors = self.extractData()
        if not errors:
            addresses = data['send_to_custom'] or []
            for group in data['send_to_groups'] or []:
                for user in api.user.get_users(groupname=group):
                    email = user.getProperty('email')
                    if email:
                        addresses.append(email)
            for username in data['send_to_users'] or []:
                user = api.user.get(username=username)
                if user:
                    email = user.getProperty('email')
                    if email:
                        addresses.append(email)

            utils = Utils(self.context, self.request)
            public_url = utils.get_public_url()
            html = data['body'].output

            filters = [f for _, f in getAdapters((self.context, self.request), IFilter)]
            html = apply_filters(filters, html)
            html = html.replace(self.context.absolute_url(), public_url.encode('utf8'))

            send_email.delay(list(set(addresses)), data['subject'], html=html)
            self.request.response.redirect('%s/@@announcements-controlpanel' % (
                self.context.absolute_url()))


class ISendEmailSubscribersForm(model.Schema):
    subject = schema.ASCIILine(
        title=u'Subject')

    directives.widget('send_to_categories', SelectFieldWidget)
    send_to_categories = schema.List(
        title=u'Send to categories',
        required=False,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )
    body = RichText(
        title=u'Body',
        description=u'Message body',
        default_mime_type='text/html',
        output_mime_type='text/html',
        allowed_mime_types=('text/html',),
        required=True,
        default=RichTextValue(
            u'<p></p><p></p>'
            u'<p><a href="{{change_url}}">Change your subscription settings</a></p>'
            u'<p><a href="{{unsubscribe_url}}">Unsubscribe from these messages</a></p>',
            'text/html', 'text/html'))


class SendEmailSubscribersForm(AutoExtensibleForm, form.Form):
    schema = ISendEmailSubscribersForm

    ignoreContext = True

    @button.buttonAndHandler(u'Send', name='send2')
    def handle_send2(self, action):
        data, errors = self.extractData()
        if not errors:
            utils = Utils(self.context, self.request)
            public_url = utils.get_public_url()
            html = data['body'].output

            filters = [f for _, f in getAdapters((self.context, self.request), IFilter)]
            html = apply_filters(filters, html)
            html = html.replace(self.context.absolute_url(), public_url.encode('utf8'))

            categories = set()
            if 'form.widgets.send_to_categories' in self.request.form:
                categories = set(self.request.form['form.widgets.send_to_categories'])

            send_email_to_subscribers.delay(data['subject'], html=html, categories=categories)

            api.portal.show_message(
                'Sending emails', request=self.request, type='info')
            self.request.response.redirect('%s/@@announcements-controlpanel' % (
                self.context.absolute_url()))


class ISendTextForm(model.Schema):

    text = schema.Text(
        title=u'Text message')


class SendTextForm(AutoExtensibleForm, form.Form):

    schema = ISendTextForm

    ignoreContext = True

    @button.buttonAndHandler(u'Send', name='text')
    def handle_text(self, action):
        data, errors = self.extractData()
        if not errors:
            texting.send(data['text'], ALL_SUBSCRIBERS)
            api.portal.show_message(
                'Text message sent', request=self.request, type='info')
            self.request.response.redirect('%s/@@announcements-controlpanel' % (
                self.context.absolute_url()))


class AnnouncementsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = AnnouncementsControlPanelForm
    index = ViewPageTemplateFile('templates/announcements.pt')

    hasTexting = False

    def __init__(self, context, request):
        super(AnnouncementsControlPanel, self).__init__(context, request)
        self.email_form = SendEmailUsersForm(aq_inner(context), request)
        self.email_subscribers_form = SendEmailSubscribersForm(aq_inner(context), request)
        self.text_subscribers_form = SendTextForm(aq_inner(context), request)

    def __call__(self):
        registry = getUtility(IRegistry)
        if (registry.get('castle.plivo_auth_id') and
                registry.get('castle.plivo_auth_token') and
                registry.get('castle.plivo_phone_number')):
            self.hasTexting = True
        self.email_form.update()
        self.email_subscribers_form.update()
        self.text_subscribers_form.update()
        return super(AnnouncementsControlPanel, self).__call__()
