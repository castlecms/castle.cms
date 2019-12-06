from castle.cms.cron._pw_expiry import update_password_expiry
from plone.registry import Registry
from plone.registry import field
from plone.registry import Record
from plone import api


def upgrade(context, logger=None):
    try:
        auth_step_timeout = api.portal.get_registry_record(name='plone.auth_step_timeout', default=None)
    except api.exc.InvalidParameterError:
        auth_step_timeout = None

    if not auth_step_timeout:
        registry = Registry()
        auth_timeout_field = field.Int(title=u"(Seconds) This amount of inactivity \
                                                will reset the login process",
                                       description=u"Between each step, the allowed \
                                                     time is reset to this amount",
                                       default=120)
        auth_timeout_record = Record(auth_timeout_field)
        registry.records['plone.auth_step_timeout'] = auth_timeout_record

    update_password_expiry(api.portal.get())
