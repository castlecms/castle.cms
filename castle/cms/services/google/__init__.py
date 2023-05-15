import ast
import httplib2
import json
import logging
import os
import random
import subprocess

from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from oauth2client.client import SignedJwtAssertionCredentials
from plone import api
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

def get_ga4_data(ga_id, paths, form, params):
    output = None
    registry = getUtility(IRegistry)

    environ = os.environ.copy()
    environ['GOOGLE_ANALYTICS_PROPERTY_ID'] = ga_id
    environ['GOOGLE_ANALYTICS_API_EMAIL'] = registry.get('castle.google_api_email', None)
    environ['GOOGLE_ANALYTICS_PATHS'] = str(paths)
    environ['GOOGLE_ANALYTICS_PARAMS'] = str(params)

    # Get credentials from control panel if not provided via env variable
    if not os.environ.get('GOOGLE_API_KEY', None):
        api_key = registry.get('castle.google_api_service_key_file', None)
        if api_key is None:
            logger.error('No service key file provided for GA4 Data API')
            return
        environ['GOOGLE_API_KEY'] = api_key

    form_params = json.loads(form['params'])
    form_type = form['type'].upper()

    if form_type == 'GA':
        form_type = 'HISTORICAL'
    environ['CASTLE_GA_FORM_TYPE'] = form_type

    for key, val in form_params.items():
        if key == 'metrics' or key == 'dimensions':
            val = str(val)
            if val.startswith('-'):
                val = val.replace('-', '')
            environ['GA_%s_%s' % (form_type, str(key.upper()))] = val
        else:
            environ['GA_%s_%s' % (form_type, str(key.upper()))] = str(val)

    command = ['/usr/bin/python3', 'scripts/google/google-api.py']
    
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

    output = ast.literal_eval(output.replace('\n', ''))
    return output


def get_mock_ga4_data(paths, form):
    data = {'rows': []}
    form_params = json.loads(form['params'])
    if form_params['global']:
        for path in paths:
            data['rows'].append([path, random.randrange(0, 50)])
    else:
        path = api.portal.get().absolute_url_path()
        data['rows'].append([path, random.randrange(0, 50)])
    return data
