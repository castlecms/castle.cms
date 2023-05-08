import ast
import json
import logging
import os
import subprocess

import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from oauth2client.client import SignedJwtAssertionCredentials
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


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

def get_ga4_data(request, ga_id):
    output = None
    command = ['/usr/bin/python3', 'scripts/google/google-api.py']

    environ = os.environ.copy()
    environ['GOOGLE_ANALYTICS_PROPERTY_ID'] = ga_id

    # Get credentials from control panel if not provided via env variable
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', None):
        registry = getUtility(IRegistry)
        api_key = registry.get('castle.google_data_api_service_key_file', None)
        if api_key is None:
            logger.error('No service key file provided for GA4 Data API')
            return
        environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key

    form = request.form
    params = json.loads(form['params'])
    form_type = form['type'].upper()

    if form_type == 'GA':
        form_type = 'HISTORICAL'
    environ['CASTLE_GA_FORM_TYPE'] = form_type

    for key, val in params.items():
        if key == 'metrics' or key == 'dimensions':
            val = str(val)
            if val.startswith('-'):
                val = val.replace('-', '')
            environ['GA_%s_%s' % (form_type, str(key.upper()))] = val
        else:
            environ['GA_%s_%s' % (form_type, str(key.upper()))] = str(val)

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

    output = ast.literal_eval(output.replace('\n', ''))
    return output
