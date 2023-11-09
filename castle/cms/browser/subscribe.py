from castle.cms import subscribe
from castle.cms import texting
from castle.cms.utils import get_random_string
from castle.cms.utils import send_email
from castle.cms.utils import verify_recaptcha
from castle.cms.widgets import ReCaptchaFieldWidget
from plone import api
from plone.app.users.schema import checkEmailAddress
from plone.autoform.form import AutoExtensibleForm
from plone.autoform.directives import widget
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import ISiteSchema
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from urllib import urlencode
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form import interfaces
from z3c.form.action import ActionErrorOccurred
from z3c.form.interfaces import WidgetActionExecutionError
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope import schema
from zope.component import getUtility
from zope.component import queryUtility
from zope.event import notify
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.interface import Invalid

import phonenumbers
import string


def check_phone_number(val):
    if not val:
        return
    number = ''.join([l for l in val if l in string.digits])  # noqa: E741

    if len(number) == 10:
        number = '1' + number

    number = '+' + number
    try:
        number = phonenumbers.parse(number, None)
    except Exception:
        raise Invalid('Not a valid phone number')

    if not phonenumbers.is_valid_number(number):
        raise Invalid('Not a valid phone number')
    return True


class ISubscribeForm(Interface):
    name = schema.ASCIILine(
        title=u'Full name',
        description=u'',
        required=True)

    email = schema.ASCIILine(
        title=u'E-mail',
        description=u'',
        required=True,
        constraint=checkEmailAddress)

    phone_number = schema.TextLine(
        title=u'Phone number',
        description=u'If you would like to receive text message alerts. ',
        required=False,
        constraint=check_phone_number)

    widget(
        'categories',
        CheckBoxFieldWidget,
    )
    categories = schema.List(
        title=u'Categories',
        description=u"Select the types of content you'd like to receive.",
        required=True,
        value_type=schema.Choice(
            vocabulary='castle.cms.vocabularies.EmailCategories'
        )
    )

    captcha = schema.TextLine(
        title=u"Captcha",
        required=False)


class BaseForm(AutoExtensibleForm, form.Form):

    def send_text_message(self, subscriber):
        registry = getUtility(IRegistry)
        site_settings = registry.forInterface(ISiteSchema,
                                              prefix="plone",
                                              check=False)
        text_message = '%s phone verification code: %s' % (
            site_settings.site_title,
            subscriber['code'][-6:])
        return texting.send(text_message, subscriber['phone_number'])


class SubscribeForm(BaseForm):
    label = u"Subscribe"
    description = u"Subscribe to this site for notifications"
    formErrorsMessage = 'There were errors.'
    ignoreContext = True
    schema = ISubscribeForm
    template = ViewPageTemplateFile('templates/subscribe.pt')
    sent = False
    subscribed = False

    def __init__(self, context, request):
        super(SubscribeForm, self).__init__(context, request)
        registry = queryUtility(IRegistry)
        self.has_captcha = registry.get('castle.recaptcha_private_key') not in (None, '')
        self.has_texting = registry.get('castle.plivio_auth_id') not in (None, '')
        self.isAnon = None

    def send_mail(self, email, categories, username='User', code=None):

        registry = getUtility(IRegistry)
        site_settings = registry.forInterface(ISiteSchema,
                                              prefix="plone",
                                              check=False)
        url = '%s/@@subscribe?confirmed_email=%s&confirmed_code=%s&categories=%s' % (
            self.context.absolute_url(), email, code, categories)
        text = """
Copy and paste this url into your web browser to confirm your address: %s
""" % url
        html = """
<p>Hi %s,</p><br>
<p>You have requested subscription to: <strong>%s</strong>.</p>
<p>Please <a href="%s">confirm your email address by clicking on this link</a>.
</p>
<p>
If that does not work, copy and paste this url into your web browser: <i>%s</i>
</p>""" % (username, ', '.join(categories), url, url)
        send_email(
            [email], "Email Confirmation for subscription(%s)" % site_settings.site_title,
            html=html, text=text)

    def updateFields(self):
        super(SubscribeForm, self).updateFields()
        if self.isAnon is None:
            portal_membership = getToolByName(self.context, 'portal_membership')
            self.isAnon = portal_membership.isAnonymousUser()

        if self.has_captcha and self.isAnon:
            self.fields['captcha'].widgetFactory = ReCaptchaFieldWidget
        else:
            self.fields['captcha'].mode = interfaces.HIDDEN_MODE
        if not self.has_texting:
            self.fields['phone_number'].mode = interfaces.HIDDEN_MODE

    @button.buttonAndHandler(u'Subscribe', name='subscribe')
    def action_subscribe(self, action):
        data, errors = self.extractData()

        # Checks if the user is already subscribed to certain categories
        # and will show an error if so.
        try:
            subscriber = subscribe.get_subscriber(data.get('email'))
            if subscriber:
                try:
                    already_subscribed = set(subscriber['categories']).intersection(
                        set(self.request.form['form.widgets.categories']))
                    if already_subscribed:
                        notify(
                            ActionErrorOccurred(
                                action,
                                WidgetActionExecutionError('email', Invalid(
                                    'User already subscribed to %s' % ', '.join(already_subscribed)))))
                        return
                except KeyError:
                    self.status = self.formErrorsMessage
        except AttributeError:
            self.status = self.formErrorsMessage

        if 'name' not in data:
            notify(
                ActionErrorOccurred(
                    action,
                    WidgetActionExecutionError('name', Invalid('Must input a name'))))

        try:
            if data['categories'] == []:
                notify(
                    ActionErrorOccurred(
                        action,
                        WidgetActionExecutionError('categories', Invalid(
                            'At least one category must be selected.'))))
        except KeyError:
            self.status = self.formErrorsMessage

        if self.has_captcha and self.isAnon:
            if not verify_recaptcha(self.request):
                notify(
                    ActionErrorOccurred(
                        action,
                        WidgetActionExecutionError('captcha', Invalid('Invalid Recaptcha'))))
                return

        if errors:
            self.status = self.formErrorsMessage

        try:
            # Generate a random string for the url code.
            url_code = get_random_string(8)

            # User data from the submitted form
            email = self.request.form['form.widgets.email']
            categories = self.request.form['form.widgets.categories']
            name = self.request.form['form.widgets.name']

            if name != '':
                subscribe.register(email, {'categories': categories}, url_code)

                self.send_mail(email, categories, name, url_code)

                self.sent = True
                api.portal.show_message(
                    'Verification email has been sent to your email', request=self.request, type='info')
            else:
                api.portal.show_message(
                    'Must enter name, email, and select at least one category',
                    request=self.request, type='error'
                )
        except Exception:
            api.portal.show_message(
                'Must enter name, email, and select at least one category',
                request=self.request, type='error')

    def __call__(self):
        registry = queryUtility(IRegistry)
        self.subscriptions_enabled = registry.get(
            'plone.enable_notification_subscriptions', False)
        portal_membership = getToolByName(self.context, 'portal_membership')
        self.isAnon = portal_membership.isAnonymousUser()

        if not self.has_captcha or not self.subscriptions_enabled:
            api.portal.show_message(
                """Subscriptions are not enabled on this site. Enable them in site control panel.
                    Recaptcha must also be enabled""",
                request=self.request, type='error')
            return self.request.response.redirect(self.context.absolute_url())
        if 'confirmed_code' in self.request.form and 'confirmed_email' in self.request.form:

            try:
                alsoProvides(self.request, IDisableCSRFProtection)

                subscribe.confirm(self.request.form['confirmed_email'],
                                  self.request.form['confirmed_code'])
                api.portal.show_message('Successfully subscribed to portal', request=self.request)
                self.subscribed = True
            except subscribe.InvalidEmailException:
                api.portal.show_message('Invalid Email', request=self.request, type='error')
            except subscribe.InvalidCodeException:
                api.portal.show_message('Invalid Code', request=self.request, type='error')

        return super(SubscribeForm, self).__call__()


class IConfirmPhoneForm(Interface):

    email = schema.ASCIILine(
        title=u'E-mail',
        description=u'',
        required=True,
        constraint=checkEmailAddress)

    phone_number = schema.TextLine(
        title=u'Phone number',
        description=u'Change number and click re-send to use a different number',
        constraint=check_phone_number)

    phone_number_code = schema.TextLine(
        title=u'Code',
        description=u'Code that was texted to your phone',
        required=False)


class ConfirmPhoneForm(BaseForm):
    label = u"Confirm phone number"
    description = u""
    schema = IConfirmPhoneForm
    template = ViewPageTemplateFile('templates/subscribe-phone.pt')
    confirmed = False
    formErrorsMessage = 'There were errors.'
    ignoreContext = True

    def updateFields(self):
        super(ConfirmPhoneForm, self).updateFields()
        self.fields['email'].mode = interfaces.HIDDEN_MODE

    @button.buttonAndHandler(u'Confirm', name='subscribe')
    def action_subscribe(self, action):
        data, errors = self.extractData()

        subscriber = subscribe.get_subscriber(data['email'])
        if errors:
            return

        if subscriber.get('phone_number') != data['phone_number']:
            subscriber['phone_number'] = data['phone_number']
            if not self.send_text_message(subscriber):
                api.portal.show_message('Error sending code', request=self.request, type='error')
            else:
                api.portal.show_message('Phone number changed, code re-sent',
                                        request=self.request, type='info')

        if not data.get('phone_number_code'):
            ActionErrorOccurred(
                action,
                WidgetActionExecutionError('phone_number_code', Invalid('No code specified')))

        if not errors:
            try:
                alsoProvides(self.request, IDisableCSRFProtection)
                subscribe.confirm_phone_number(data['email'], data['phone_number_code'])
                self.confirmed = True
                api.portal.show_message(
                    'Phone number successfully confirmed', request=self.request, type='info')
            except subscribe.InvalidEmailException:
                api.portal.show_message('Invalid Email', request=self.request, type='error')
            except subscribe.InvalidCodeException:
                api.portal.show_message('Invalid Code', request=self.request, type='error')

    @button.buttonAndHandler(u'Re-send', name='resend')
    def action_resend(self, action):
        data, errors = self.extractData()

        subscriber = subscribe.get_subscriber(data['email'])
        if errors:
            return

        if subscriber.get('phone_number') != data['phone_number']:
            subscriber['phone_number'] = data['phone_number']

        if not self.send_text_message(subscriber):
            api.portal.show_message('Error sending code', request=self.request, type='error')
        else:
            api.portal.show_message('Code sent', request=self.request, type='info')


class ChangeSubscription(form.EditForm):
    schema = ISubscribeForm
    fields = field.Fields(ISubscribeForm)
    label = u"Edit you subscription settings"
    ignoreContext = True
    validUser = True
    user = None
    email = None
    code = None

    def __init__(self, context, request):
        super(ChangeSubscription, self).__init__(context, request)

        if 'code' in request.form and 'email' in request.form:
            self.email = self.request.form['email']
            self.code = self.request.form['code']

            self.setUser()
            self.validateUser()
        else:
            api.portal.show_message('Invalid URL', request=self.request, type='error')
            self.validUser = False
            return

    def action(self):
        url = self.context.absolute_url() + '/@@changesubscription?'
        url += urlencode({
            'code': self.user['code'],
            'email': self.user['email']
        })
        return url

    @button.buttonAndHandler(u'Apply', name='apply')
    def action_apply(self, action):
        prefix = 'form.widgets.'
        user = subscribe.get(self.request.form[prefix + 'email'])
        form = self.request.form

        changed_items = ['phone_number', 'name', 'categories']

        for item in changed_items:
            if prefix + item in form:
                user[item] = form[prefix + item]
                self.widgets[item].value = form[prefix + item]
            else:
                # The categories widget isn't included if it's empty
                user[item] = []
                self.widgets[item].value = []

        self.widgets['categories'].update()

        api.portal.show_message('Subscription settings changed', request=self.request, type='info')

    def getContent(self):
        if not self.validUser:
            return

        return self.user

    def setUser(self):
        self.user = subscribe.get(self.email)

    def validateUser(self):
        if self.user['code'] != self.code:
            api.portal.show_message('Invalid URL', request=self.request, type='error')
            self.validUser = False

    def updateWidgets(self):
        super(ChangeSubscription, self).updateWidgets()
        if not self.validUser:
            return

        form_items = ['email', 'name', 'phone_number', 'categories']
        for item in form_items:
            self.widgets[item].value = self.user[item]

        self.widgets['categories'].update()

        self.widgets['email'].mode = interfaces.HIDDEN_MODE
        self.widgets['captcha'].mode = interfaces.HIDDEN_MODE


class Unsubscribe(BrowserView):
    unsubscribed = False
    error = None

    def __call__(self):
        form = self.request.form
        if 'code' in form and 'email' in form:
            email = form['email']
            subscriber = subscribe.get(email)
            if subscriber:
                if subscriber.get('code') == form['code']:
                    alsoProvides(self.request, IDisableCSRFProtection)
                    subscribe.remove(email)
                    self.unsubscribed = True
                else:
                    self.error = 'Invalid unsubscribe url'
        return super(Unsubscribe, self).__call__()
