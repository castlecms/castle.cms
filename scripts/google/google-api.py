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

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)


logger = logging.getLogger("app")

def sample_run_report():
    """Runs a simple report on a Google Analytics 4 property."""
    property_id = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", None)

    if not property_id:
        logger.error('GOOGLE_ANALYTICS_PROPERTY_ID environment variable must be set')

    # Using a default constructor instructs the client to use the credentials
    # specified in GOOGLE_APPLICATION_CREDENTIALS environment variable.
    client = BetaAnalyticsDataClient()

    import pdb; pdb.set_trace()

    # request = RunReportRequest(
    #     property=f"properties/{property_id}",
    #     dimensions=[Dimension(name="city")],
    #     metrics=[Metric(name="activeUsers")],
    #     date_ranges=[DateRange(start_date="2020-03-31", end_date="today")],
    # )
    # response = client.run_report(request)

    # print("Report result:")
    # for row in response.rows:
    #     print(row.dimension_values[0].value, row.metric_values[0].value)
