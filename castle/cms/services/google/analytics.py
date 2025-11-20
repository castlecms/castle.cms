import json
import os
import random
import tempfile
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from google.analytics.admin_v1alpha.types import ListPropertiesRequest
from google.oauth2 import service_account
from plone import api
from plone.formwidget.namedfile.converter import b64decode_file
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


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


def get_mock_ga4_data(params):
    paths = []
    site_contents = api.portal.get().listFolderContents()
    for page in site_contents:
        paths.append(page.absolute_url_path())

    data = {'rows': []}
    if params['global']:
        for path in paths:
            data['rows'].append([path, random.randrange(0, 50)])
    else:
        path = api.portal.get().absolute_url_path()
        data['rows'].append([path, random.randrange(0, 50)])
    return data

