from castle.cms.commands import docsplit
from castle.cms.utils import get_data_from_url
from castle.cms.utils import inline_images_in_dom
from lxml.etree import tostring
from lxml.html import fromstring
from lxml.html.clean import Cleaner
from plone import api
from plone.app.blob.utils import openBlob
from plone.registry.interfaces import IRegistry
from ZODB.blob import Blob
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.globalrequest import getRequest

import json
import logging
import requests
import traceback


logger = logging.getLogger('castle.cms')
cleaner = Cleaner(style=True, page_structure=False,
                  processing_instructions=False, forms=False, meta=True,
                  annoying_tags=False, remove_unknown_tags=False)


def create_raw_from_view(context, view_name='pdf', css_files=[]):
    request = getRequest()
    view = getMultiAdapter((context, request), name=view_name)
    html = view()
    portal = api.portal.get()
    site_url = portal.absolute_url()
    css = []
    for css_file in css_files:
        ct, data = get_data_from_url(css_file)
        if isinstance(data, basestring):
            css.append(data)
    xml = fromstring(html)
    cleaner(xml)
    inline_images_in_dom(xml, portal, site_url)

    registry = getUtility(IRegistry)
    public_url = registry.get(
        'plone.public_url', '')

    if public_url not in ('', None):
        for anchor in xml.cssselect('a'):
            if anchor.attrib.get('href', '').startswith(site_url):
                anchor.attrib['href'] = anchor.attrib['href'].replace(site_url, public_url)

    return tostring(xml), css


class PDFGenerationError(Exception):
    pass


def create(html, css):
    try:
        registry = getUtility(IRegistry)
        prince_server_url = registry.get(
            'castle.princexml_server_url', 'http://localhost:6543/convert')
        if prince_server_url is None:
            logger.warning(
                'error converting pdf, no princexmlserver defined')
            return
        logger.info('start converting pdf')
        xml = fromstring(html)
        # save styles
        resp = requests.post(
            prince_server_url,
            data={'xml': tostring(xml), 'css': json.dumps(css)})
        if resp.status_code != 200:
            raise PDFGenerationError('status: {}, data: {}'.format(
                resp.status_code, resp.text))
        data = resp.content
        blob = Blob()
        bfile = blob.open('w')
        bfile.write(data)
        bfile.close()
        return blob
    except Exception:
        logger.info(traceback.format_exc())
        raise


def screenshot(blob):
    blobfi = openBlob(blob)
    filepath = docsplit.dump_image(blobfi.read(), '1000', 'gif')
    blobfi.close()

    blob = Blob()
    bfile = blob.open('w')
    sfi = open(filepath, 'rb')
    bfile.write(sfi.read())
    bfile.close()
    sfi.close()
    return blob
