import os
from castle.cms import cache
from castle.cms import social
from castle.cms.services.google import analytics
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    RunRealtimeReportRequest,
    DateRange,
    Dimension,
    Metric
)
from plone import api
from Products.Five import BrowserView
from zope.component import getMultiAdapter

import json


class AnalyticsView(BrowserView):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        paths = self.get_paths()
        if self.request.get('api') == 'ga':
            data = self.ga4_api_call(paths)
        else:
            data = social.get_stats(self.context)
            if data:
                data = dict(data)

        return json.dumps({
            'paths': paths,
            'data': data
        })

    def ga4_api_call(self, paths):
        params = json.loads(self.request.get('params'))

        if os.environ.get("GOOGLE_ANALYTICS_IS_DEV", False):
            return analytics.get_mock_ga4_data(params)

        cache_key = '-'.join(api.portal.get().getPhysicalPath()[1:])
        for key, value in params.items():
            cache_key += '%s=%s' % (key, value)

        try:
            result = cache.get(cache_key)
        except Exception:
            result = None

        if result is None:
            credentials = analytics.get_ga4_credentials()
            data_client = BetaAnalyticsDataClient(credentials=credentials)
            if not data_client:
                return {'error': 'Could not get GA4 data client'}
            
            admin_client = AnalyticsAdminServiceClient(credentials=credentials)
            if not admin_client:
                return {'error': 'Could not get GA4 admin client'}

            property_id = analytics.get_ga4_property(admin_client)
            if not property_id:
                return {'error': 'Could not get GA4 property'}
            
            dimension = params.get('dimensions')
            metric = params.get('metrics')
            limit = params.get('max_results')
            start_date = params.get('start_date', None)
            end_date = params.get('end_date', None)
            
            try:
                if self.request.get('type') == 'realtime':
                    response = data_client.run_realtime_report(
                        RunRealtimeReportRequest(
                            property=f"properties/{property_id}",
                            dimensions=[Dimension(name=dimension)],
                            metrics=[Metric(name=metric)],
                            limit=limit,                         
                            order_bys=[
                                {
                                    "metric": {"metric_name": metric},
                                    "desc": True
                                }
                            ]
                        )
                    )
                else:
                    response = data_client.run_report(
                        RunReportRequest(
                            property=f"properties/{property_id}",
                            dimensions=[Dimension(name=dimension)],
                            metrics=[Metric(name=metric)],
                            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                            limit=limit,
                            order_bys=[{
                                "metric": {"metric_name": metric},
                                "desc": True
                            }]
                        )
                    )

            finally:
                # Python3 TODO - Maybe cache this instead of closing it every time?
                if data_client is not None:
                    data_client.transport.grpc_channel.close() 

        return response if response.rows else None


    def get_ga_profile(self, service):
        cache_key = '%s-ga-profile' % '-'.join(api.portal.get().getPhysicalPath()[1:])
        try:
            profile = cache.get(cache_key)
        except Exception:
            profile = None
        if profile is None:
            profile = analytics.get_ga_profile(service)
            cache.set(cache_key, profile, 60 * 60 * 1)
        return profile


    def get_paths(self):
        site_path = '/'.join(api.portal.get().getPhysicalPath())
        context_path = '/'.join(self.context.getPhysicalPath())
        base_path = context_path[len(site_path):]
        paths = [base_path, base_path + '/view']

        context_state = getMultiAdapter((self.context, self.request),
                                        name='plone_context_state')
        if context_state.is_portal_root():
            paths.append('/')
            paths.append('/main-page')
        return list(set(paths))
