#!/usr/bin/env python3
"""
Build the Analytics Data Client to submit requests to and retrieve
analytics data for the site.

requires `google-analytics-data` to be installed to python environment

requires python >= 3.7 to run

Environment Variables to configure:

GOOGLE_APPLICATION_CREDENTIALS
GOOGLE_ANALYTICS_PROPERTY_ID
GOOGLE_ANALYTICS_IS_DEV
"""
import json
import logging
import os
import sys

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account


logger = logging.getLogger("google-api")
IS_DEV = os.environ.get("GOOGLE_ANALYTICS_IS_DEV", False)
PROPERTY_ID = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", None)
    
def get_mock_service_data():
    # TODO: generate mock data for dev and testing purposes...
    data = {}
    return

class GA4Service():

    def __init__(self):
        self.category = os.environ.get("CASTLE_GA_FORM_TYPE", "REALTIME")
        self.credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", None)

        if os.path.isfile(self.credentials):
            self.client = BetaAnalyticsDataClient()
        else:
            self.credentials = json.loads(self.credentials)
            self.credentials = service_account.Credentials.from_service_account_info(self.credentials)
            scoped_credentials = self.credentials.with_scopes(
                ['https://www.googleapis.com/auth/cloud-platform']
            )
            self.client = BetaAnalyticsDataClient(credentials=scoped_credentials)

    
    def get_service_data(self):
        data = {}
        dimensions = os.environ.get(f"GA_{self.category}_DIMENSIONS", None)
        metrics = os.environ.get(f"GA_{self.category}_METRICS", "screenPageViews")
        start_date = os.environ.get(f"GA_{self.category}_START_DATE", "7daysAgo")
        end_date = os.environ.get(f"GA_{self.category}_END_DATE", "today")
        max_results = os.environ.get(f"GA_{self.category}_MAX_RESULTS", 5)

        if not dimensions:
            request = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                metrics=[Metric(name=metrics)],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=max_results
            )
        else:
            request = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                dimensions=[Dimension(name=dimensions)],
                metrics=[Metric(name=metrics)],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=max_results
            )
        response = self.client.run_report(request)

        for row in response.rows:
            data[row.dimension_values[0].value] = row.metric_values[0].value

        return data


if __name__ == '__main__':
    if IS_DEV:
        service_data = get_mock_service_data()
        print(service_data)
        sys.exit()
    if not PROPERTY_ID:
        logger.error('GOOGLE_ANALYTICS_PROPERTY_ID environment variable must be set')
        sys.exit()
    service_data = GA4Service().get_service_data()
    print(service_data)
