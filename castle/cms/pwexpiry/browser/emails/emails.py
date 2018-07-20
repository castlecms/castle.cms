# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from castle.cms.pwexpiry.config import _
from zope.i18n import translate


class NotificationEmail(BrowserView):

    def __call__(self, **kwargs):
        """ A E-Mail Template,
        call this like this:

        email_template = getMultiAdapter(
            (api.portal.get(), request), name=notification_email
        )

        body = email_template(**{
            'username': user.getUserId(),
            'fullname': safe_unicode(user.getProperty('fullname')),
            'days': days_to_expire,
            'language': language_code,
        })
        """
        language = kwargs['language']

        msg_mapping = {
            'username': kwargs['username'],
            'fullname': kwargs['fullname'],
            'days': kwargs['days'],
        }

        if self.request.get('SERVER_URL', 'http://foo') == 'http://foo':
            server_url = ""
        else:
            server_url = self.request.get('SERVER_URL')

        if server_url.endswith('/'):
            server_url = server_url[:-1]

        msg_mapping['server_url'] = server_url

        if self.request.get('SERVER_NAME', 'foo') == 'foo':
            server_name = ""
        else:
            server_name = self.request.get('SERVER_NAME')

        msg_mapping['server_name'] = server_name

        if kwargs['days'] > 0:
            msg = translate(
                _('email_text',
                  default=u"""Hello ${fullname},

There are ${days} days left before your password expires!

Please ensure to reset your password before it's expired.""",
                  mapping=msg_mapping,
                  ),
                target_language=language
            )

            msg += translate(
                _('change_password_email_text',
                  default=u"""\n\nIn order to change your password, please visit ${server_url}/@@change-password""",
                  mapping=msg_mapping,
                  ),
                target_language=language
            )
        else:
            msg = translate(
                _('email_text_expired',
                  default=u"""Hello ${fullname},

Your password has expired.

Please ensure to reset your password before it's expired.""",
                  mapping=msg_mapping,
                  ),
                target_language=language
            )

            msg += translate(
                _('reset_password_email_text',
                  default=u"""\n\nIn order to reset your password, please visit ${server_url}/mail_password_form?userid=${username}""",
                  mapping=msg_mapping,
                  ),
                target_language=language
            )

        if msg_mapping['server_name'] != "":
            msg += translate(
                _('server_name_email_text',
                  default=u"""\n\nThis email was sent from ${server_name}""",
                  mapping=msg_mapping,
                  ),
                target_language=language
            )

        return msg
