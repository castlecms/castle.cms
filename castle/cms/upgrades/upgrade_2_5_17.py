from castle.cms.cron._pw_expiry import update_password_expiry
from plone.registry.interfaces import IRegistry
from plone.registry import field
from plone.registry import Record
from plone import api
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

PROFILE_ID = 'profile-castle.cms:2_5_17'


def upgrade(context, logger=None):
    setup = getToolByName(context, 'portal_setup')
    setup.runAllImportStepsFromProfile(PROFILE_ID)
    registry = getUtility(IRegistry)
    try:
        auth_step_timeout = api.portal.get_registry_record(name='plone.auth_step_timeout', default=None)
    except api.exc.InvalidParameterError:
        auth_step_timeout = None

    if not auth_step_timeout:
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

    update_password_expiry(api.portal.get())

    for id in context.objectIds():
        context[id].reindexObject(idxs=['has_private_parents'])

    try:
        scrub_site_identity = api.portal.get_registry_record(name='plone.scrub_title_logo_to_backend_login',
                                                             default=None)
    except api.exc.InvalidParameterError:
        scrub_site_identity = None

    if not scrub_site_identity:
        scrub_identity_field = field.Bool(
            title=u'Do not show identifying customizations (logo/text) at backend login view',
            description=u'If set, backend visitors will see a generic login view.',
            default=False,
            required=False)
        scrub_identity_record = Record(scrub_identity_field)
        registry._records['plone.scrub_title_logo_to_backend_login'] = scrub_identity_record

    try:
        login_footer_message = api.portal.get_registry_record(name='plone.scrub_title_logo_to_backend_login',
                                                              default=None)
    except api.exc.InvalidParameterError:
        login_footer_message = None

    if not login_footer_message:
        login_footer_message_field = field.TextLine(
            title=u'Login Footer Message',
            description=u'Display a message or warning below the secure login form',
            required=False)
        login_footer_message_record = Record(login_footer_message_field)
        registry._records['plone.login_footer_message'] = login_footer_message_record
