# overridable default settings from environment variables
import os


def get(name, default, _type='unicode'):
    env_name = 'DEFAULT_{}'.format(name.upper())
    if env_name in os.environ:
        value = os.environ[env_name]
    else:
        value = default
    if _type == 'unicode':
        if not isinstance(value, unicode):
            value = unicode(value)
    elif _type == 'bool':
        if not isinstance(value, bool):
            value = value.lower() in ('t', 'true', '1', 'on')
    return value
