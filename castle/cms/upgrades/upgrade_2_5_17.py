from castle.cms.cron._pw_expiry import update_password_expiry
from plone.registry.interfaces import IRegistry
from plone.registry import field
from plone.registry import Record
from plone import api
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
import transaction

PROFILE_ID = 'profile-castle.cms:2_5_17'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    try:
        auth_step_timeout = api.portal.get_registry_record(name='plone.auth_step_timeout', default=None)
    except api.exc.InvalidParameterError:
        auth_step_timeout = None

    if not auth_step_timeout:
        registry = getUtility(IRegistry)
        auth_timeout_field = field.Int(title=u"(Seconds) This amount of inactivity \
                                                will reset the login process",
                                       description=u"Between each step, the allowed \
                                                     time is reset to this amount",
                                       default=120)
        auth_timeout_record = Record(auth_timeout_field)
        registry._records['plone.auth_step_timeout'] = auth_timeout_record

    try:
        disclaimer = api.portal.get_registry_record(name='castle.show_disclaimer', default=None)
    except api.exc.InvalidParameterError:
        disclaimer = None

    if not disclaimer:
        registry = getUtility(IRegistry)
        show_disclaimer_field = field.Bool(
            title=u'Show disclaimer for first time a user visits a site. '
                  u'To comply with ePrivacy Directive, use this feature to notify about cookie use.',
            default=False,
            required=False)
        site_disclaimer_field = field.Text(
            title=u"Disclaimer",
            default=u'<p><strong>Disclaimer</strong> '
                    u'<em>You are seeing this because this is your first time visiting the site.</em></p>',
            required=False)
        show_disclaimer_record = Record(show_disclaimer_field)
        site_disclaimer_record = Record(site_disclaimer_field)
        registry._records['castle.show_disclaimer'] = show_disclaimer_record
        registry._records['castle.site_disclaimer'] = site_disclaimer_record
    transaction.commit()

    update_password_expiry(api.portal.get())
