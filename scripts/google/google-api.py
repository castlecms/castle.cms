#!/usr/bin/env python3
"""
Build the Analytics Data Client to submit requests to and retrieve
analytics data for the site.

requires `google-analytics-data` to be installed to python environment

requires python >= 3.7 to run

Environment Variables to configure:

GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
GOOGLE_ANALYTICS_PROPERTY_ID
"""
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


logger = logging.getLogger("google-api")
property_id = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", None)

if not property_id:
    logger.error('GOOGLE_ANALYTICS_PROPERTY_ID environment variable must be set')
    sys.exit()
    
class GA4Service():

    def __init__(self):
        # Using a default constructor instructs the client to use the credentials
        # specified in GOOGLE_APPLICATION_CREDENTIALS environment variable.
        self.client = BetaAnalyticsDataClient()
        self.category = 'REALTIME' # 'HISTORICAL', 'SOCIAL'

    
    def get_service_data(self):
        data = []
        data.append({'dimension': 'metric'})

        dimensions = os.environ.get(f"GA_{self.category}_DIMENSIONS", "N/A")
        metrics = os.environ.get(f"GA_{self.category}_AGGREGATE", "Page views")
        start_date = os.environ.get(f"GA_{self.category}_START_DATE", "7daysAgo")
        end_date = os.environ.get(f"GA_{self.category}_END_DATE", "today")
        max_results = os.environ.get(f"GA_{self.category}_MAX_RESULTS", 5)

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name=dimensions)],
            metrics=[Metric(name=metrics)],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            max=max_results
            )
        response = self.client.run_report(request)

        for row in response.rows:
            data.append({row.dimension_values[0].value: row.metric_values[0].value})

        return data


if __name__ == '__main__':
    service_data = GA4Service().get_service_data()
    print(service_data)
