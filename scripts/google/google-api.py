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


logger = logging.getLogger("app")
property_id = os.environ.get("GOOGLE_ANALYTICS_PROPERTY_ID", None)

if not property_id:
    logger.error('GOOGLE_ANALYTICS_PROPERTY_ID environment variable must be set')
    
else:
    # Using a default constructor instructs the client to use the credentials
    # specified in GOOGLE_APPLICATION_CREDENTIALS environment variable.
    client = BetaAnalyticsDataClient()

    print(client)
