#!/usr/bin/env python3
"""
Build the Analytics Data Client to submit requests to and retrieve
analytics data for the site.

requires python >= 3.7 to run

environment dependencies:
google-api-python-client==2.2.0
PyCryptodome==3.17
google-auth-httplib2==0.1.0
google-auth-oauthlib==1.0.0 

Environment Variables to configure:

GOOGLE_CLIENT_ID
"""
import ast
import logging
import os
import sys

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


logger = logging.getLogger('google-api')

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", None)


def ga_auth(scopes):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('scripts/google/credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('analyticsdata', 'v1beta', credentials=creds)

    return service


def get_service_data():
    category = os.environ.get("CASTLE_GA_FORM_TYPE", "REALTIME")
    current_url_path = os.environ.get("GOOGLE_ANALYTICS_CURRENT_URL_PATH", "/")
    paths = os.environ.get("GOOGLE_ANALYTICS_PATHS", None)
    params = os.environ.get("GOOGLE_ANALYTICS_PARAMS", None)
    params = ast.literal_eval(params)
    scopes = ['https://www.googleapis.com/auth/analytics.readonly']
    report_data = {'rows': []}
    service = ga_auth(scopes)

    request = {
        'metrics': [{'name': params['metrics']}],
        'limit': params['max_results']
    }

    try:
        request['dimensions'] = [{'name': params['dimensions']}]
    except KeyError:
        pass        

    if category == 'HISTORICAL':
        request['dateRanges'] = {
            'startDate': params['start_date'],
            'endDate': params['end_date']
        }
        if params['global']:
            # use pagePath dimension when getting data for all available site paths
            request['dimensions'] = [{'name': 'pagePath'}]
            request['dimensionFilter'] = {
                'filter': {
                    'fieldName': 'pagePath',
                    'stringFilter': {
                        'matchType': 'CONTAINS',
                        'value': current_url_path
                    }
                }
            }
            for path in paths:
                request['dimensionFilter']['filter']['stringFilter']['value'] = path
                response = service.properties().runReport(
                    property=f'properties/{GOOGLE_CLIENT_ID}',
                    body=request).execute()
                try:
                    report_data['rows'].append([path, response['rows']['metricValues']['value']])
                except KeyError:
                    pass
            if report_data['rows'] == []:
                report_data = None
        else:
            response = service.properties().runReport(
                property=f'properties/{GOOGLE_CLIENT_ID}',
                body=request).execute()
            try:
                report_data['rows'].append([current_url_path, response['rows']['metricValues']['value']])
            except KeyError:
                report_data = None
    elif category == 'REALTIME':
        if params['global']:
            logger.error('"pagePath" dimension is unavailabe for realtime reporting with Data API (GA4).')
        response = service.properties().runRealtimeReport(
            property=f'properties/{GOOGLE_CLIENT_ID}',
            body=request).execute()
        try:
            report_data['rows'].append([current_url_path, response['rows']['metricValues']['value']])
        except KeyError:
            report_data = None
    elif category == 'SOCIAL':
        # TODO: handle social tab.
        import pdb; pdb.set_trace()
    else:
        return None
    
    return report_data


if __name__ == '__main__':
    if not GOOGLE_CLIENT_ID:
        sys.exit()
    service_data = get_service_data()
    print(service_data)
