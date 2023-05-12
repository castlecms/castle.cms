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
pandas==2.0.1

openssl pkcs12 -in castledev-6dc6c022d790.p12 -nocerts -passin pass:notasecret -nodes -out privatekey.pem

Environment Variables to configure:

GOOGLE_API_KEY
GOOGLE_ANALYTICS_PROPERTY_ID
GOOGLE_CLIENT_SECRET
GOOGLE_CLIENT_ID
GOOGLE_ANALYTICS_IS_DEV
"""
import ast
import base64
import httplib2
import json
import logging
import os
import pandas as pd
import sys

from apiclient.discovery import build
from apiclient.http import HttpMock
from collections import defaultdict
# from oauth2client.client import OAuth2Credentials
# from oauth2client.client import SignedJwtAssertionCredentials



import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


logger = logging.getLogger("google-api")

IS_DEV = os.environ.get("GOOGLE_ANALYTICS_IS_DEV", False)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", None)
GOOGLE_API_EMAIL = os.environ.get("GOOGLE_ANALYTICS_API_EMAIL", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", None)


def get_mock_service_data():
    http = HttpMock('analyticsdata-discovery.json', {'status': '200'})
    api_key = GOOGLE_API_KEY
    service = build('analyticsdata', 'v1beta', http=http, developerKey=api_key)

    import pdb; pdb.set_trace()

class GA4Service():

    def __init__(self):
        self.category = os.environ.get("CASTLE_GA_FORM_TYPE", "REALTIME")
        self.paths = os.environ.get("GOOGLE_ANALYTICS_PATHS", None)
        self.params = os.environ.get("GOOGLE_ANALYTICS_PARAMS", None)
    
    def get_service_data(self):
        scopes = ['https://www.googleapis.com/auth/analytics.readonly']
        service = self.ga_auth(scopes)

        params = ast.literal_eval(self.params)

        try:
            dimensions = [params['dimensions']]
        except KeyError:
            dimensions = []
        metrics = [params['metrics']]
        
        request = {
            "requests": [
                {
                "dateRanges": [
                    {
                    "startDate": "2022-03-01",
                    "endDate": "2022-03-31"
                    }
                ],
                "dimensions": [{'name': name} for name in dimensions],
                "metrics": [{'name': name} for name in metrics],
                "limit": 100000
                }
            ]
        }

        response = service.properties().batchRunReports(property=f'properties/{GOOGLE_CLIENT_ID}', body=request).execute()
        report_data = defaultdict(list)

        for report in response.get('reports', []):
            rows = report.get('rows', [])
            for row in rows:
                for i, key in enumerate(dimensions):
                    report_data[key].append(row.get('dimensionValues', [])[i]['value'])  # Get dimensions
                for i, key in enumerate(metrics):
                    report_data[key].append(row.get('metricValues', [])[i]['value'])  # Get metrics

        return report_data


    def ga_auth(self, scopes):
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

if __name__ == '__main__':
    if IS_DEV:
        service_data = get_mock_service_data()
        print(service_data)
        sys.exit()
    if not GOOGLE_CLIENT_ID and not GOOGLE_API_KEY:
        sys.exit()
    service_data = GA4Service().get_service_data()
    print(service_data)
