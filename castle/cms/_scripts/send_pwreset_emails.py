"""
For resetting multiple user account passwords (by sending a password reset email
to their account's configured address)
"""
from argparse import ArgumentParser
import logging
import os
from smtplib import SMTPException
from smtplib import SMTPRecipientsRefused

from AccessControl.SecurityManagement import newSecurityManager
from chameleon import PageTemplate
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component import getUtility
from zope.component.hooks import setSite

import transaction

# ripped from https://github.com/plone/Products.CMFPlone/blob/master/Products/CMFPlone/RegistrationTool.py
try:
    # Products.MailHost has a patch to fix quoted-printable soft line breaks.
    # See https://github.com/zopefoundation/Products.MailHost/issues/35
    from Products.MailHost.MailHost import message_from_string
except ImportError:
    # If the patch is ever removed, we fall back to the standard library.
    from email import message_from_string


logger = logging.getLogger("Plone")


def get_args():
    parser = ArgumentParser(
        description='Get a report of permissions by role and user')
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    parser.add_argument('--users-file', dest='users_file', default=None)
    parser.add_argument('--ident-field', dest='ident_field', choices=['userid', 'username'], default='username')  # noqa
    parser.add_argument('--base-url', dest='base_url', default=None)  # noqa
    args, _ = parser.parse_known_args()
    assert args.base_url is not None
    assert args.users_file is not None
    return args


mail_password_reset_template_str = """<tal:root
>From: <span tal:replace="structure encoded_mail_sender" />
To: <span tal:replace="python:member.getProperty('email')" />
Subject: <span tal:replace="mail_password_subject" />
Content-Type: text/html
Precedence: bulk

<p>
  The following link will take you to a page where you can reset your password for <span
      tal:omit-tag=""
      tal:content="navigation_root_title" /> site:

  <a href="${base_url}/@@password-reset?code=${reset.randomstring}&userid=${member.id}">
    ${base_url}/@@password-reset?code=${reset.randomstring}&userid=${member.id}
  </a>
</p>

<p>
  (This link is valid for <span tal:content="expiration_timeout" tal:omit-tag="" /> hours)
</p>

<p>
  If you didn't expect to receive this email, please ignore it. Your password has not been changed.
</p>

</tal:root>
"""
mail_password_reset_template = PageTemplate(mail_password_reset_template_str)


# basically ripped from https://github.com/plone/Products.CMFPlone/blob/master/Products/CMFPlone/RegistrationTool.py  # noqa
def mail_password(site, req, member, base_url):
    # Rather than have the template try to use the mailhost, we will
    # render the message ourselves and send it from here (where we
    # don't need to worry about 'UseMailHost' permissions).
    reset_tool = getToolByName(site, "portal_password_reset")
    reset = reset_tool.requestReset(member.getId())

    registry = getUtility(IRegistry)

    encoding = registry.get("plone.email_charset", "utf-8")

    kwargs = {
        "base_url": base_url,
        "reset": reset,
        "password": member.getPassword(),
        "charset": encoding,
        "member": member,
        "navigation_root_title": site.Title(),
        "expiration_timeout": reset_tool.getExpirationTimeout(),
        "encoded_mail_sender": api.portal.get_registry_record('plone.email_from_address', default=''),
        "mail_password_subject": "Password reset request",
    }

    mail_text = mail_password_reset_template(**kwargs)

    # The mail headers are not properly encoded we need to extract
    # them and let MailHost manage the encoding.
    message_obj = message_from_string(mail_text.strip())
    subject = message_obj["Subject"]
    m_to = message_obj["To"]
    m_from = message_obj["From"]
    msg_type = message_obj.get("Content-Type", "text/plain")
    host = getToolByName(site, "MailHost")
    try:
        host.send(
            mail_text,
            m_to,
            m_from,
            subject=subject,
            charset=encoding,
            immediate=True,
            msg_type=msg_type,
        )
    except SMTPRecipientsRefused:
        # Don't disclose email address on failure
        raise SMTPRecipientsRefused("Recipient address rejected by server.")
    except SMTPException as e:
        raise (e)


def send_reset_emails(site, users_file, ident_field, req, base_url):
    regtool = api.portal.get_tool('portal_registration')
    acl_users = api.portal.get_tool('acl_users')
    with open(users_file, 'r') as fin:
        for ident in fin.readlines():
            kwargs = {}
            kwargs[ident_field] = ident.strip()
            member = api.user.get(**kwargs)
            if member is None:
                logger.warn("not found (skipping): {}".format(ident))
                continue
            transaction.begin()
            pw = regtool.generatePassword()
            roles = member.getRoles()
            domains = member.getDomains()
            acl_users.userFolderEditUser(
                member.getId(),
                pw,
                roles,
                domains)
            req.form['new_password'] = pw
            mail_password(site, req, member, base_url)
            transaction.commit()


def run(app):
    singleton.SingleInstance('reportusers')

    args = get_args()

    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))

    if args.site_id.strip().lower() == "_all_":
        for oid in app.objectIds():
            obj = app[oid]
            if IPloneSiteRoot.providedBy(obj):
                setSite(obj)
                send_reset_emails(obj, args.users_file, args.ident_field, app.REQUEST, args.base_url)
    else:
        site = app[args.site_id]
        setSite(site)
        send_reset_emails(site, args.users_file, args.ident_field, app.REQUEST, args.base_url)


def setup_and_run():
    conf_path = os.getenv("ZOPE_CONF_PATH", "parts/instance/zope.conf")
    if conf_path is None or not os.path.exists(conf_path):
        raise Exception('Could not find zope.conf at {}'.format(conf_path))

    from Zope2 import configure
    configure(conf_path)
    import Zope2
    app = Zope2.app()
    from Testing.ZopeTestCase.utils import makerequest
    app = makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    from zope.globalrequest import setRequest
    setRequest(app.REQUEST)
    from AccessControl.SpecialUsers import system as user
    from AccessControl.SecurityManagement import newSecurityManager
    newSecurityManager(None, user)

    run(app)


if __name__ == '__main__':
    run(app)  # noqa: F821
