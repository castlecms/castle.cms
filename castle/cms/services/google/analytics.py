from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.data import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from plone.formwidget.namedfile.converter import b64decode_file
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from . import get_service

def get_ga_service(ga_scope=['https://www.googleapis.com/auth/analytics.readonly']):
    registry = getUtility(IRegistry)
    api_email = registry.get('castle.google_api_email', None)
    api_key = registry.get('castle.google_api_service_key_file', None)
    ga_id = registry.get('castle.google_analytics_id', None)
    ua_id = registry.get('castle.universal_analytics_id', None)

    if not api_key or not api_email or (not ga_id and not ua_id):
        return
    return get_service(
        'analytics', 'v3', ga_scope, b64decode_file(api_key)[1], api_email)


def get_ga_profile(service):
    registry = getUtility(IRegistry)
    ga_id = registry.get('castle.google_analytics_id', None)
    ua_id = registry.get('castle.universal_analytics_id', None)
    if not ga_id:
        if ua_id:
            ga_id = ua_id
        else:
            return

    # Use the Analytics service object to get the first profile id.

    # Get a list of all Google Analytics accounts for this user
    accounts = service.management().accounts().list().execute()

    if accounts.get('items'):
        # Get the first Google Analytics account.
        account = accounts.get('items')[0].get('id')

        # Get a list of all the properties for the first account.
        properties = service.management().webproperties().list(
            accountId=account).execute()

        for item in properties['items']:
            if ga_id == item['id']:
                # Get a list of all views (profiles) for the first property.
                profiles = service.management().profiles().list(
                    accountId=account,
                    webPropertyId=ga_id).execute()

                if profiles.get('items'):
                    # return the first view (profile) id.
                    return profiles.get('items')[0].get('id')

    return None


def get_ga4_profile(service):
    registry = getUtility(IRegistry)
    ga_id = registry.get('castle.google_analytics_id', None)
    if not ga_id:
        return

    admin_client = AnalyticsAdminServiceClient()
    accounts = admin_client.list_accounts()
    accounts = list(admin_client.list_accounts())
    first_account = accounts[0]
    if first_account:
        properties = admin_client.list_properties(parent=first_account.name)
        for prop in properties:
            print(f"  Property: {prop.name} ({prop.display_name})")
            
            if prop.name.endswith(ga_id):
                property_id = prop.name.split('/')[-1]

                request = RunReportRequest(
                    property=f"properties/{property_id}",
                    dimensions=[{"name": "city"}],
                    metrics=[{"name": "activeUsers"}],
                    limit=5,
                )

                response = service.run_report(request)
                for row in response.rows:
                    print(row.dimension_values[0].value, row.metric_values[0].value)

    return None
