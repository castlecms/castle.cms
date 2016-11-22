from castle.cms import registration
from castle.cms.utils import get_email_from_address
from castle.cms.utils import send_email
from castle.cms.utils import verify_recaptcha
from castle.cms.widgets import ReCaptchaFieldWidget
from plone.app.users.browser.register import RegistrationForm as BaseRegistrationForm
from plone.app.users.schema import checkEmailAddress
from plone.autoform.form import AutoExtensibleForm
from plone.registry.interfaces import IRegistry
from plone.z3cform.fieldsets import utils as z3cform_utils
from plone.z3cform.fieldsets.utils import move
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form import interfaces
from z3c.form.action import ActionErrorOccurred
from z3c.form.interfaces import WidgetActionExecutionError
from zope import schema
from zope.component import getUtility
from zope.component import queryUtility
from zope.event import notify
from zope.interface import Interface
from zope.interface import Invalid


class IEmailConfirmation(Interface):
    email = schema.ASCIILine(
        title=_(u'label_email', default=u'E-mail'),
        description=u'',
        required=True,
        constraint=checkEmailAddress)

    captcha = schema.TextLine(
        title=u"Captcha",
        required=False)


class EmailConfirmation(AutoExtensibleForm, form.Form):
    label = u"Confirm your email address"
    description = (u"Before you can begin the registration process, you need to "
                   u"verify your email address.")
    formErrorsMessage = _('There were errors.')
    ignoreContext = True
    schema = IEmailConfirmation
    enableCSRFProtection = True
    template = ViewPageTemplateFile('templates/confirm-email.pt')
    sent = False

    def __init__(self, context, request):
        super(EmailConfirmation, self).__init__(context, request)
        registry = queryUtility(IRegistry)
        self.has_captcha = registry.get('castle.recaptcha_private_key') is not None
        portal_membership = getToolByName(self.context, 'portal_membership')
        self.isAnon = portal_membership.isAnonymousUser()

    def send_mail(self, email, item):
        url = '%s/@@register?confirmed_email=%s&confirmed_code=%s' % (
            self.context.absolute_url(), email, item['code'])
        text = """
Copy and paste this url into your web browser to confirm your address: %s
""" % url
        html = """
<p>You have requested registration, please
<a href="%s">confirm your email address by clicking on this link</a>.
</p>
<p>
If that does not work, copy and paste this urls into your web browser: %s
</p>""" % (url, url)
        send_email(
            [email], "Email Confirmation",
            html=html, text=text)

    def updateFields(self):
        super(EmailConfirmation, self).updateFields()
        if self.has_captcha and self.isAnon:
            self.fields['captcha'].widgetFactory = ReCaptchaFieldWidget
        else:
            self.fields['captcha'].mode = interfaces.HIDDEN_MODE

        move(self, 'email', before='*')

    @button.buttonAndHandler(
        _(u'label_verify', default=u'Verify'), name='verify'
    )
    def action_verify(self, action):
        data, errors = self.extractData()
        registry = queryUtility(IRegistry)
        has_captcha = registry.get('castle.recaptcha_private_key') is not None
        if has_captcha:
            if not verify_recaptcha(self.request):
                notify(
                    ActionErrorOccurred(
                        action,
                        WidgetActionExecutionError('captcha', Invalid('Invalid Recaptcha'))))
                return

        if not errors:
            storage = registration.RegistrationStorage(self.context)
            item = storage.add(data['email'])
            self.send_mail(data['email'], item)
            self.sent = True
            IStatusMessage(self.request).addStatusMessage(
                'Verification email has been sent to your email.', type='info')


class IHiddenVerifiedEmail(Interface):

    confirmed_email = schema.TextLine()
    confirmed_code = schema.TextLine()


class RegistrationForm(BaseRegistrationForm):

    def get_confirmed_email(self):
        req = self.request
        return req.form.get('confirmed_email', req.form.get('form.widgets.confirmed_email', ''))

    def get_confirmed_code(self):
        req = self.request
        return req.form.get(
            'confirmed_code', req.form.get('form.widgets.confirmed_code', ''))

    def verify(self):
        email = self.get_confirmed_email()
        code = self.get_confirmed_code()
        if not email or not code:
            return False
        storage = registration.RegistrationStorage(self.context)
        entry = storage.get(email)
        if entry is None:
            return False
        if entry['code'] == code:
            return True
        return False

    def updateWidgets(self):
        if self.showForm:
            super(RegistrationForm, self).updateWidgets()
        else:
            form.Form.updateWidgets(self)
        self.widgets['confirmed_email'].value = self.get_confirmed_email()
        self.widgets['confirmed_code'].value = self.get_confirmed_code()

    def validate_registration(self, action, data):
        super(RegistrationForm, self).validate_registration(action, data)

        if 'email' in data and data['email'].lower() != self.get_confirmed_email().lower():
            err_str = u'Email address you have entered does not match email used in verification'
            notify(
                ActionErrorOccurred(
                    action, WidgetActionExecutionError('email', Invalid(err_str))
                )
            )
        del data['confirmed_email']
        del data['confirmed_code']

    def handle_join_success(self, data):
        email = self.get_confirmed_email()
        storage = registration.RegistrationStorage(self.context)
        storage.remove(email)
        registry = getUtility(IRegistry)
        try:
            review = registry['plone.review_registrations']
        except KeyError:
            review = False
            pass
        if review:
            storage = registration.RegistrationReviewStorage(self.context)
            storage.add(email, data)
            self.send_email_to_admin_to_review(email)
            self.request.response.redirect('%s/@@under-review?email=%s' % (
                self.context.absolute_url(), email))
        else:
            return super(RegistrationForm, self).handle_join_success(data)

    def send_email_to_admin_to_review(self, email):
        url = '%s/@@review-registration-requests' % (
            self.context.absolute_url())
        text = """
Hi,

A new user with the email %(email)s has signed up.

You can review the request at %(url)s
""" % {
            'url': url,
            'email': email
        }
        html = """
<p>Hi,</p>

A new user with the email %(email)s has signed up.

Please <a href="%s">review the request</a>

</p>""" % {
            'url': url,
            'email': email
        }
        send_email(
            [get_email_from_address()], "User registration needs review",
            html=html, text=text)

    def updateFields(self):
        super(RegistrationForm, self).updateFields()
        if self.showForm:
            z3cform_utils.add(self, IHiddenVerifiedEmail, prefix="")
        else:
            self.fields = field.Fields(IHiddenVerifiedEmail, prefix="")
        self.fields['confirmed_email'].mode = interfaces.HIDDEN_MODE
        self.fields['confirmed_code'].mode = interfaces.HIDDEN_MODE

    def __call__(self):
        if not self.verify():
            return self.request.response.redirect('%s/@@register-confirm-email' % (
                self.context.absolute_url()))

        return super(RegistrationForm, self).__call__()


class ReviewRequests(BrowserView):

    def enabled(self):
        registry = getUtility(IRegistry)
        try:
            return registry['plone.review_registrations']
        except KeyError:
            return False

    def send_approve_mail(self, email, data):
        data = data.copy()
        text = """
Hello %(fullname)s,

The user with username "%(username)s" has been approved.

You can visit the site at: %(url)s
""" % data
        html = """
<p>Hello %(fullname)s,</p>

<p>The user with username "%(username)s" has been approved.</p>

<p>You can visit the site at: <a href="%(url)s">%(url)s</a>
</p>""" % data
        send_email(
            [email], "User approved",
            html=html, text=text)

    def __call__(self):
        storage = registration.RegistrationReviewStorage(self.context)
        if self.request.REQUEST_METHOD == 'POST':
            email = self.request.form.get('email')
            if self.request.form.get('approve'):
                data = storage.get(email).copy()
                data.pop('code')
                data.pop('created')
                reg_form = BaseRegistrationForm(self.context, self.request)
                reg_form.updateFields()
                reg_form.updateWidgets()
                reg_form.handle_join_success(data)
                if data.get('password'):
                    # won't get an email so sent them out something about getting approved
                    self.send_approve_mail(email, data)
                storage.remove(email)
            elif self.request.form.get('deny'):
                storage.remove(email)
            elif self.request.form.get('enable'):
                getUtility(IRegistry)['plone.review_registrations'] = True
            elif self.request.form.get('disable'):
                getUtility(IRegistry)['plone.review_registrations'] = False
        self.storage = storage
        self.data = storage._data
        return self.index()


class UnderReview(BrowserView):

    def __call__(self):
        storage = registration.RegistrationReviewStorage(self.context)
        self.data = storage.get(self.request.form.get('email'))
        return self.index()
