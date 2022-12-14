from pkg_resources import get_distribution


def get_castle_version(strip_dev=False):
    version_number = get_distribution('castle.cms').version
    if strip_dev:
        version_parts = version_number.split('.')
        is_dev_version = version_parts[-1].find('dev') == 0
        return_version_parts = version_parts[:-1 if is_dev_version else None]
        return '.'.join(return_version_parts)
    return version_number


CASTLE_VERSION = get_castle_version()
CASTLE_VERSION_STRING = 'CastleCMS {}'.format(CASTLE_VERSION)
