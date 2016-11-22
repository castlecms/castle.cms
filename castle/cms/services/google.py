from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials
from plone.formwidget.namedfile.converter import b64decode_file
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import httplib2


def get_service(api_name, api_version, scope, key, service_account_email):
    """Get a service that communicates to a Google API.

    Args:
        api_name: The name of the api to connect to.
        api_version: The api version to connect to.
        scope: A list auth scopes to authorize for the application.
        key_file_location: The path to a valid service account p12 key file.
        service_account_email: The service account email address.

    Returns:
        A service that is connected to the specified API.
    """

    credentials = SignedJwtAssertionCredentials(
        service_account_email, key, scope=scope)

    http = credentials.authorize(httplib2.Http())

    # Build the service object.
    service = build(api_name, api_version, http=http)

    return service


def get_ga_service(ga_scope=['https://www.googleapis.com/auth/analytics.readonly']):
    registry = getUtility(IRegistry)
    api_email = registry.get('castle.google_api_email', None)
    api_key = registry.get('castle.google_api_service_key_file', None)
    ga_id = registry.get('castle.google_analytics_id', None)

    if not api_key or not api_email or not ga_id:
        return

    # Authenticate and construct service.
    return get_service(
        'analytics', 'v3', ga_scope, b64decode_file(api_key)[1], api_email)


def get_ga_profile(service):
    registry = getUtility(IRegistry)
    ga_id = registry.get('castle.google_analytics_id', None)
    if not ga_id:
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
