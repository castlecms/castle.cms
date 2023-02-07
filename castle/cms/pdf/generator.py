from castle.cms.commands import docsplit
from castle.cms.utils import get_data_from_url
from castle.cms.utils import inline_images_in_dom
from lxml.etree import tostring
from lxml.html import fromstring
from lxml.html.clean import Cleaner
from plone.app.blob.utils import openBlob
from plone.registry.interfaces import IRegistry
from requests.auth import HTTPBasicAuth
from ZODB.blob import Blob
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.globalrequest import getRequest

import json
import logging
import plone.api as api
import requests
import traceback


logger = logging.getLogger('castle.cms')
cleaner = Cleaner(
    style=True,
    page_structure=False,
    processing_instructions=False,
    forms=False,
    meta=True,
    annoying_tags=False,
    remove_unknown_tags=False,
)


def create_raw_from_view(context, view_name='pdf', css_files=None, unrestricted_traverse=False):
    if css_files is None:
        css_files = []
    request = getRequest()
    view = getMultiAdapter((context, request), name=view_name)
    html = view()
    portal = api.portal.get()
    site_url = portal.absolute_url()
    css = []
    for css_file in css_files:
        ct, data = get_data_from_url(
            url=css_file,
            unrestricted_traverse=unrestricted_traverse,
        )
        if isinstance(data, basestring):
            css.append(data.replace('\n', ''))
    xml = cleaner.clean_html(fromstring(html))
    inline_images_in_dom(
        dom=xml,
        portal=portal,
        site_url=site_url,
        unrestricted_traverse=unrestricted_traverse,
    )

    registry = getUtility(IRegistry)
    public_url = registry.get('plone.public_url', '')

    if public_url not in ('', None):
        for anchor in xml.cssselect('a'):
            if anchor.attrib.get('href', '').startswith(site_url):
                anchor.attrib['href'] = anchor.attrib['href'].replace(site_url, public_url)

    return (tostring(xml), css)


class PDFGenerationError(Exception):
    pass


def get_prince_server_settings():
    registry = api.portal.get_tool('portal_registry')
    return {
        'url': registry.get(
            'castle.princexml_server_url',
            'http://localhost:6543/convert',
        ),
        'username': registry.get('castle.princexml_server_auth_username', '') or '',
        'password': registry.get('castle.princexml_server_auth_password', '') or '',
    }


def create(html, css, additional_args={}):
    try:
        server_settings = get_prince_server_settings()
        if not server_settings['url']:
            logger.warning('error converting pdf, no princexmlserver defined')
            return
        logger.info('start converting pdf')
        xml = fromstring(html)

        response = requests.post(
            server_settings['url'],
            data=json.dumps({
                'xml': tostring(xml),
                'css': css,
                'additional_args': additional_args,
            }),
            auth=HTTPBasicAuth(
                server_settings['username'],
                server_settings['password'],
            ),
        )
        if response.status_code != 200:
            raise PDFGenerationError(
                'status: {}, data: {}'.format(
                    response.status_code,
                    response.text,
                )
            )
        data = response.content
        blob = Blob()
        blob_file = blob.open('w')
        blob_file.write(data)
        blob_file.close()
        return blob
    except Exception:
        logger.info(traceback.format_exc())
        raise


def screenshot(blob):
    blob_file = openBlob(blob)
    filepath = docsplit.dump_image(blob_file.read(), '1000', 'gif')
    blob_file.close()

    blob = Blob()
    new_blob_file = blob.open('w')
    screenshot_file = open(filepath, 'rb')
    new_blob_file.write(screenshot_file.read())
    new_blob_file.close()
    screenshot_file.close()
    return blob
