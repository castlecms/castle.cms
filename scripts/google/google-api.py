#!/usr/bin/env python3
"""
Build the Analytics Data Client to submit requests to and retrieve
analytics data for the site.

requires python >= 3.7 to run

environment dependencies:
google-api-python-client==2.2.0
oauth2client==1.5.2
pycrypto==2.6.1

Environment Variables to configure:

GOOGLE_API_KEY
GOOGLE_ANALYTICS_PROPERTY_ID
GOOGLE_CLIENT_SECRET
GOOGLE_CLIENT_ID
GOOGLE_ANALYTICS_IS_DEV
"""
import base64
import httplib2
import logging
import os
import sys

from apiclient.discovery import build
from apiclient.http import HttpMock
from oauth2client.client import OAuth2Credentials
from oauth2client.client import SignedJwtAssertionCredentials


logger = logging.getLogger("google-api")

IS_DEV = os.environ.get("GOOGLE_ANALYTICS_IS_DEV", False)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", None)
GOOGLE_API_EMAIL = os.environ.get("GOOGLE_ANALYTICS_API_EMAIL", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", None)


def get_mock_service_data():
    http = HttpMock('analytics-data.json', {'status': '200'})
    api_key = GOOGLE_API_KEY
    service = build('analyticsdata', 'v1beta', http=http, developerKey=api_key)
    request = service.volumes().list(source='public', q='android')
    response = request.execute(http=http)
    return response


def b64decode_file(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    filename, data = value.split(b";")

    filename = filename.split(b":")[1]
    filename = base64.standard_b64decode(filename)
    filename = filename.decode("utf-8")

    data = data.split(b":")[1]
    data = base64.standard_b64decode(data)

    return filename, data


class GA4Service():

    def __init__(self):
        self.category = os.environ.get("CASTLE_GA_FORM_TYPE", "REALTIME")
        self.paths = os.environ.get("GOOGLE_ANALYTICS_PATHS", None)
        self.params = os.environ.get("GOOGLE_ANALYTICS_PARAMS", None)
    
    def get_service_data(self):
        ga_scope='https://www.googleapis.com/auth/analytics.readonly'

        if not GOOGLE_API_KEY or not GOOGLE_API_EMAIL or not GOOGLE_CLIENT_ID:
            return
        else:
            service = self.get_service('analyticsdata', 'v1beta', ga_scope, b64decode_file(GOOGLE_API_KEY)[1], GOOGLE_API_EMAIL)
        if not service:
            return {'error': 'Could not get GA Service'}

        profile = self.get_ga_profile(service)
        if not profile:
            return {'error': 'Could not get GA Profile'}

        if self.request.get('type') == 'realtime':
            ga = service.data().realtime()
            if not self.params.pop('global', False):
                # need to restrict by filters
                path_query = ','.join(['rt:pagePath==%s' % p for p in self.paths])
                self.params['filters'] = path_query
        else:
            if not self.params.pop('global', False):
                # need to restrict by filters
                path_query = ','.join(['ga:pagePath==%s' % p for p in self.paths])
                self.params['filters'] = path_query
            ga = service.data().ga()

        query = ga.get(ids='ga:' + profile, **self.params)
        result = query.execute()

        return result

    def get_service(self, api_name, api_version, scope, key=None,
                    service_account_email=None, access_token=None,
                    refresh_token=None, token_expiry=None):
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

    def get_ga_profile(self, service):
        # Use the Analytics service object to get the first profile id.

        # Get a list of all Google Analytics accounts for this user
        profile = None
        import pdb; pdb.set_trace()
        accounts = service.management().accounts().list().execute()

        if accounts.get('items'):
            # Get the first Google Analytics account.
            account = accounts.get('items')[0].get('id')

            # Get a list of all the properties for the first account.
            properties = service.management().webproperties().list(
                accountId=account).execute()

            for item in properties['items']:
                if GOOGLE_CLIENT_ID == item['id']:
                    # Get a list of all views (profiles) for the first property.
                    profiles = service.management().profiles().list(
                        accountId=account,
                        webPropertyId=GOOGLE_CLIENT_ID).execute()

                    if profiles.get('items'):
                        # return the first view (profile) id.
                        profile = profiles.get('items')[0].get('id')

        return profile


if __name__ == '__main__':
    if IS_DEV:
        service_data = get_mock_service_data()
        print(service_data)
        sys.exit()
    if not GOOGLE_CLIENT_ID and not GOOGLE_API_KEY:
        sys.exit()
    service_data = GA4Service().get_service_data()
    print(service_data)
