import os

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from oauth2client.client import SignedJwtAssertionCredentials


GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')


def get_service(api_name, api_version, scope, key=None,
                service_account_email=None, access_token=None,
                refresh_token=None, token_expiry=None):
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
    service = None

    if key and service_account_email:
        credentials = SignedJwtAssertionCredentials(
            service_account_email, key, scope=scope)

        http = credentials.authorize(httplib2.Http())

        # Build the service object.
        service = build(api_name, api_version, http=http)
    elif GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        creds = OAuth2Credentials(
            access_token=access_token, client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET, refresh_token=refresh_token,
            token_uri='https://accounts.google.com/o/oauth2/token',
            token_expiry=token_expiry, user_agent='Castle CMS')
        http = creds.authorize(httplib2.Http())
        service = build(api_name, api_version, http=http)

    return service
