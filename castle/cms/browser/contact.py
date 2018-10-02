from Products.CMFPlone.browser import contact_info
from Products.CMFPlone.browser.interfaces import IContactForm as IBaseContactForm
from Products.statusmessages.interfaces import IStatusMessage
from castle.cms.utils import verify_recaptcha
from castle.cms.widgets import ReCaptchaFieldWidget
from plone import api
from plone.registry.interfaces import IRegistry
from z3c.form import button
from z3c.form import field
from z3c.form.action import ActionErrorOccurred
from z3c.form.interfaces import HIDDEN_MODE
from z3c.form.interfaces import WidgetActionExecutionError
from zope import schema
from zope.component import getUtility
from zope.event import notify
from zope.interface import Invalid


class IContactForm(IBaseContactForm):
    captcha = schema.TextLine(
        title=u"Captcha",
        required=False)


class ContactForm(contact_info.ContactForm):

    fields = field.Fields(IContactForm)

    def update(self):
        super(ContactForm, self).update()
        registry = getUtility(IRegistry)
        has_captcha = registry.get('castle.recaptcha_private_key') is not None
        if not has_captcha:
            self.fields['captcha'].mode = HIDDEN_MODE
        else:
            self.fields['captcha'].widgetFactory = ReCaptchaFieldWidget

    @button.buttonAndHandler(u'Send', name='send')
    def handle_send(self, action):
        data, errors = self.extractData()

        registry = getUtility(IRegistry)
        has_captcha = registry.get('castle.recaptcha_private_key') is not None

        if has_captcha:
            if not verify_recaptcha(self.request):
                notify(
                    ActionErrorOccurred(
                        action,
                        WidgetActionExecutionError('captcha', Invalid('Invalid Recaptcha'))))
                return

        if errors:
            IStatusMessage(self.request).add(
                self.formErrorsMessage,
                type=u'error'
            )

            return

        self.send_message(data)
        self.send_feedback()
        self.success = True

    def render(self):
        registry = getUtility(IRegistry)
        if registry.get('plone.disable_contact_form', False):
            self.request.response.redirect(api.portal.get().absolute_url())
        return super(ContactForm, self).render()
