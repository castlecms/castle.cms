import logging
import os
import subprocess

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from oauth2client.client import SignedJwtAssertionCredentials


logger = logging.getLogger('google-service')

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

def get_ga4_service(ga_id):
    output = None
    command = ['/usr/bin/python3', 'scripts/google/google-api.py']

    environ = os.environ.copy()
    environ['GOOGLE_ANALYTICS_PROPERTY_ID'] = ga_id

    # TODO: get data from Content Analytics modal form to set values for report

    # realtime
    environ['GA_REALTIME_AGGREGATE'] = 'Page views'
    environ['GA_REALTIME_DIMENSIONS'] = 'N/A'
    environ['GA_REALTIME_MAX_RESULTS'] = '5'
    environ['GA_REALTIME_CHART_TYPE'] = 'Columns'
    # historical
    environ['GA_HISTORICAL_AGGREGATE'] = 'Page views'
    environ['GA_HISTORICAL_DIMENSIONS'] = 'N/A'
    environ['GA_HISTORICAL_MAX_RESULTS'] = '5'
    environ['GA_HISTORICAL_CHART_TYPE'] = 'Columns'
    environ['GA_HISTORICAL_START_DATE'] = '2023-04-13'
    environ['GA_HISTORICAL_END_DATE'] = '2023-04-20'
    # social
    environ['GA_SOCIAL_AGGREGATE'] = 'Page views'
    environ['GA_SOCIAL_DIMENSIONS'] = 'N/A'
    environ['GA_SOCIAL_MAX_RESULTS'] = '5'
    environ['GA_SOCIAL_CHART_TYPE'] = 'Columns'
    environ['GA_SOCIAL_START_DATE'] = '2023-04-13'
    environ['GA_SOCIAL_END_DATE'] = '2023-04-20'

    try:
        process = subprocess.Popen(
            command,
            env=environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        output, error = process.communicate()
        if error:
            logger.error(error)
        if not output:
            logger.error('No output received from GA4 request')
            return
    except ImportError:
        # /usr/bin/pip3 install google-analytics-data
        logger.error('google-analytics-data package not installed into environment')

    output = output.split('\n')
    
    return output
