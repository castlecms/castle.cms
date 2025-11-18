import os
import tempfile
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from google.analytics.admin_v1alpha.types import ListPropertiesRequest
from google.oauth2 import service_account
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


def get_ga4_credentials():
    registry = getUtility(IRegistry)
    api_key = registry.get('castle.google_api_service_key_file', None)
    service_account_email = registry.get('castle.google_api_email', None)

    if not api_key:
        raise ValueError("No Google API service key found in registry")

    filename, key_bytes = b64decode_file(api_key)
    if not key_bytes:
        raise ValueError("Decoded key file is empty")

    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]

    # .JSON
    if key_bytes.strip().startswith(b"{"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(key_bytes)
            tmp.flush()
            key_path = tmp.name

        credentials = service_account.Credentials.from_service_account_file(
            key_path, scopes=scopes
        )
        os.unlink(key_path)
        return credentials

    # .p12 (legacy)
    if not service_account_email:
        raise ValueError("Service account email is required for .p12 keys")

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        key_bytes, b"notasecret", backend=default_backend()
    )
    if not private_key:
        raise ValueError("No private key found in .p12 data")

    # serialize private key from .p12 file manually
    key_info = {
        "type": "service_account",
        "client_email": service_account_email,
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
    }

    credentials = service_account.Credentials.from_service_account_info(
        key_info, scopes=scopes
    )
    return credentials


def get_ga4_property(admin_client):
    registry = getUtility(IRegistry)
    ga_id = registry.get('castle.google_analytics_id', None)
    if not ga_id:
        return

    accounts = list(admin_client.list_accounts())
    first_account = accounts[0]
    if first_account:
        request = ListPropertiesRequest(
            filter=f"parent:{first_account.name}"
        )
        properties = admin_client.list_properties(request=request)
        for prop in properties:
            if prop.name.endswith(ga_id):
                property_id = prop.name.split('/')[-1]
                return property_id

    return None
