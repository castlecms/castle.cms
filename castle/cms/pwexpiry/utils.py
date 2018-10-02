# -*- coding: utf-8 -*-
import pytz
from castle.cms.pwexpiry.config import _
from plone import api
from Products.CMFPlone.utils import safe_unicode
from zope.component import getMultiAdapter
from zope.i18n import translate


def send_notification_email(user, days_to_expire,
                            email_view='notification_email'):
    """
    """

    language = api.portal.get_default_language()
    if user.getProperty('language'):
        language = user.getProperty('language')

    recipient = user.getProperty('email')
    portal = api.portal.get()

    email_template = getMultiAdapter(
        (portal, portal.REQUEST), name=email_view
    )

    body = email_template(**{
        'username': user.getUserId(),
        'fullname': safe_unicode(user.getProperty('fullname')),
        'days': days_to_expire,
        'language': language,
    })

    subject = translate(
        _('email_subject',
          default=u"${days} days left to password expiration",
          mapping={'days': days_to_expire},
          ),
        target_language=language
    )

    api.portal.send_email(recipient=recipient,
                          subject=subject,
                          body=body)


def days_since_event(event_date, current_date):
    """
    Returns the number of days difference
    between two given dates
    """
    # make both dates timezone aware
    if not event_date.tzinfo:
        event_date = pytz.utc.localize(event_date)
    if not current_date.tzinfo:
        current_date = pytz.utc.localize(current_date)

    difference = current_date - event_date
    return difference.days
