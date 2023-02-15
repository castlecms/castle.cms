from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html2text import html2text
from logging import getLogger

from castle.cms.constants import ALL_SUBSCRIBERS
from castle.cms.constants import ALL_USERS

import plone.api as api

logger = getLogger('castle.cms')


def get_email_from_address():
    return api.portal.get_registry_record(
        'plone.email_from_address',
        default='',
    )


def send_email(recipients=None, subject=None, html='', text='', sender=None):
    sender = get_sender(sender)
    text = get_text(text, html)
    message = get_message(subject, sender, text, html)

    mailhost = api.portal.get_tool('MailHost')
    send_mail = getattr(mailhost, 'send', lambda x: logger.warn('could not find mailhost.send'))

    for recipient in get_cleaned_recipients(recipients):
        message['To'] = recipient
        send_mail(message.as_string())


def get_cleaned_recipients(recipients=None):
    if recipients is None:
        recipients = []
    elif isinstance(recipients, basestring):
        recipients = [recipients]

    cleaned_recipients = set()
    for recipient in recipients:
        cleaned_recipients.update(get_email_addresses(recipient))
    return get_formatted_email_addresses(cleaned_recipients)


def get_email_addresses(recipient):
    if recipient == ALL_USERS:
        return [
            user.getProperty('email')
            for user in api.user.get_users()
            if user.getProperty('email')
        ]
    if recipient == ALL_SUBSCRIBERS:
        from castle.cms import subscribe
        return subscribe.get_email_addresses()
    return [recipient]


def get_formatted_email_addresses(recipients):
    users = get_all_users()
    return [
        users.get(recipient, recipient)
        for recipient in recipients
    ]


def get_all_users():
    users = {}
    for user in api.user.get_users():
        try:
            get_property = getattr(user, 'getProperty', lambda x: None)
            email = get_property('email')
            if not email:
                continue
            full_name = get_property('fullname')
            if not full_name:
                email_address = email
            else:
                email_address = '{full_name}<{email}>'.format(
                    full_name=full_name,
                    email=email,
                )
            users[email] = email_address
        except Exception:
            continue
    return users


def get_text(text='', html=''):
    if bool(text) and not bool(html):
        try:
            text = html2text(html)
        except Exception:
            pass
    return text


def get_sender(sender=None):
    if sender is None:
        sender = get_email_from_address()
    users = get_all_users()
    return users.get(sender, sender)


def get_message(subject, sender, text, html):
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = sender
    if text:
        part = MIMEText(text, 'plain')
        message.attach(part)
    if html:
        part = MIMEText(html, 'html')
        message.attach(part)
    return message
