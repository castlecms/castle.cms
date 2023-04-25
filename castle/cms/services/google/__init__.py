import json
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

def get_ga4_service(request, ga_id):
    output = None
    command = ['/usr/bin/python3', 'scripts/google/google-api.py']

    environ = os.environ.copy()
    environ['GOOGLE_ANALYTICS_PROPERTY_ID'] = ga_id

    form = request.form
    params = json.loads(form['params'])
    form_type = form['type'].upper()

    if form_type == 'GA':
        form_type = 'HISTORICAL'
    environ['CASTLE_GA_FORM_TYPE'] = form_type

    property_conversion_mapping = get_property_conversion_mapping()

    for key, val in params.items():
        if key == 'metrics' or key == 'dimensions':
            try:
                val = str(val)
                if val.startswith('-'):
                    val = val.replace('-', '')
                property_val = property_conversion_mapping[val]
                environ['GA_%s_%s' % (form_type, str(key.upper()))] = property_val
            except KeyError:
                logger.error('No available property conversion for %s' % val)
                return
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

    output = output.split('\n')
    
    return output


def get_property_conversion_mapping():
    # TODO:
    #! = exact property unavailable for Data API V1
    # available dimension and metric values:
    # https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema
    # https://ga-dev-tools.google/dimensions-metrics-explorer/

    property_conversion_mapping = {
        # Realtime
        # Dimensions
        'rt:userType': 'userGender', #!
        'rt:medium': 'medium',
        'rt:trafficType': 'contentType', #!
        'rt:browser': 'browser',
        'rt:operatingSystem': 'operatingSystem',
        'rt:deviceCategory': 'deviceCategory',
        'rt:country': 'country',
        'rt:region': 'region',
        'rt:pagePath': 'pagePath',
        # Metrics
        'rt:pageViews': 'screenPageViews',
        'rt:activeUsers': 'activeUsers',

        # Historical
        # Dimensions
        'ga:userType': 'userGender', #!
        'ga:sessionCount': 'sessions',
        'ga:socialNetwork': 'sourcePlatform', #!
        'ga:hasSocialSourceReferral': 'sessionSourceMedium', #!
        'ga:medium': 'medium',
        'ga:trafficType': 'contentType', #!
        'ga:browser': 'browser',
        'ga:operatingSystem': 'operatingSystem',
        'ga:deviceCategory': 'deviceCategory',
        'ga:pagePath': 'pagePath',
        'ga:country': 'country',
        'ga:region': 'region',
        'ga:continent': 'continent',
        'ga:subContinent': '', #!? continent?
        'ga:metro': '', #!? method?
        'ga:city': 'city',
        'ga:flashVersion': '', #!? appVersion?
        'ga:javaEnabled': '', #!? visible?
        'ga:language': 'language',
        'ga:exitPagePath': 'pagePath',
        # Metrics
        'ga:hits': 'checkouts', #!
        'ga:users': 'totalUsers',
        'ga:newUsers': 'newUsers',
        'ga:sessions': 'sessions',
        'ga:pageviews': 'screenPageViews',
        'ga:bounces': '', #!? bounceRate?
        'ga:bounceRate': 'bounceRate',
        'ga:avgSessionDuration': 'averageSessionDuration',
        'ga:entranceRate': '', #!? bounceRate?
        'ga:pageviewsPerSession': 'screenPageViewsPerSession',
        'ga:avgTimeOnPage': 'engagementRate', #!
        'ga:avgPageLoadTime': '' #!?engagementRate?
    }
    return property_conversion_mapping
