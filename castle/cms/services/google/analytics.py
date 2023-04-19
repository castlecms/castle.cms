from plone.formwidget.namedfile.converter import b64decode_file
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from . import get_ga4_service
from . import get_service


def get_ga_service(ga_scope=['https://www.googleapis.com/auth/analytics.readonly']):
    registry = getUtility(IRegistry)
    api_email = registry.get('castle.google_api_email', None)
    api_key = registry.get('castle.google_api_service_key_file', None)
    ga_id = registry.get('castle.google_analytics_id', None)
    ua_id = registry.get('castle.universal_analytics_id', None)

    if not api_key or not api_email or (not ga_id and not ua_id):
        return
    if ga_id:
        return get_ga4_service(ga_id)
    elif ua_id:
        return get_service(
            'analytics', 'v3', ga_scope, b64decode_file(api_key)[1], api_email)


def get_ga_profile(service):
    registry = getUtility(IRegistry)
    ga_id = registry.get('castle.google_analytics_id', None)
    ua_id = registry.get('castle.universal_analytics_id', None)
    if ga_id:
        return get_ga4_profile(service, ga_id)
    else:
        if ua_id:
            ga_id = ua_id
        else:
            return

    # Use the Analytics service object to get the first profile id.

    # Get a list of all Google Analytics accounts for this user
    accounts = service.management().accounts().list().execute()

    if accounts.get('items'):
        # Get the first Google Analytics account.
        account = accounts.get('items')[0].get('id')

        # Get a list of all the properties for the first account.
        properties = service.management().webproperties().list(
            accountId=account).execute()

        for item in properties['items']:
            if ga_id == item['id']:
                # Get a list of all views (profiles) for the first property.
                profiles = service.management().profiles().list(
                    accountId=account,
                    webPropertyId=ga_id).execute()

                if profiles.get('items'):
                    # return the first view (profile) id.
                    return profiles.get('items')[0].get('id')

    return None


def get_ga4_profile(service, ga_id):
    # TODO: Use the GA4 service object to get the first profile id.
    return
