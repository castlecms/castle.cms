from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from castle.cms.constants import ALL_SUBSCRIBERS
from castle.cms.constants import ALL_USERS
from html2text import html2text
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from zope.component import getUtility

import plone.api as api


def get_email_from_address():
    registry = getUtility(IRegistry)
    mail_settings = registry.forInterface(IMailSchema, prefix='plone')
    return mail_settings.email_from_address


def send_email(recipients=None, subject=None, html='', text='', sender=None):
    if isinstance(recipients, basestring):
        recipients = [recipients]

    cleaned_recipients = set()
    for recipient in recipients:
        if recipient == ALL_USERS:
            for user in api.user.get_users():
                email = user.getProperty('email')
                if email:
                    cleaned_recipients.add(email)
        elif recipient == ALL_SUBSCRIBERS:
            from castle.cms import subscribe
            cleaned_recipients.update(subscribe.get_email_addresses())
        else:
            cleaned_recipients.add(recipient)

    if sender is None:
        sender = get_email_from_address()

    if not text and html:
        try:
            text = html2text(html)
        except Exception:
            pass

    for recipient in cleaned_recipients:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        if text:
            part = MIMEText(text, 'plain')
            msg.attach(part)
        if html:
            part = MIMEText(html, 'html')
            msg.attach(part)

        mailhost = api.portal.get_tool('MailHost')
        mailhost.send(msg.as_string())
