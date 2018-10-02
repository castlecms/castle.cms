from plone.namedfile.file import NamedBlobImage
from unidecode import unidecode
from AccessControl.SecurityManagement import newSecurityManager
from lxml.html import fromstring
from lxml.html import tostring
from plone import api
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.app.textfield.value import RichTextValue
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.component import getUtility
from zope.component.hooks import setSite

import argparse
import random
import re
import requests
import transaction


url_regex = re.compile(
    r'^(?:http)s?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # noqa
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--file', dest='file', default=False)
parser.add_argument('--site-id', dest='site_id', default='Plone')
parser.add_argument('--limit', dest='limit', default=20, type=int)
args, _ = parser.parse_known_args()

user = app.acl_users.getUser('admin')  # noqa
newSecurityManager(None, user.__of__(app.acl_users))  # noqa
site = app[args.site_id]  # noqa
setSite(site)

container = site

normalizer = getUtility(IIDNormalizer)

resp = requests.get('https://en.wikipedia.org/wiki/Main_Page')
base_dom = dom = fromstring(resp.content)
parsed = []

while len(parsed) < args.limit:
    # find a link, parse it
    found_url = None
    while found_url is None:
        anchors = dom.cssselect('#bodyContent a')
        if len(anchors) == 0:
            anchors = base_dom.cssselect('#bodyContent a')
        anchor = random.choice(anchors)
        url = anchor.attrib.get('href')
        if (url.startswith('//') or 'Template:' in url or 'Wikipedia:' in url or  # noqa
                'Category:' in url or 'index.php' in url or 'File:' in url or
                'Help:' in url or 'Portal:' in url or 'Talk:' in url):
            continue
        if url and url[0] == '/':
            url = 'https://en.wikipedia.org' + url
        if (url and url_regex.match(url) and url not in parsed and
                url.startswith('https://en.wikipedia.org')):
            found_url = url

    # randomly decide to make new folder to put stuff in
    if random.randint(0, 100) > 90:  # 10% chance
        container = api.content.create(
            type='Folder', title='Folder', container=container,
            exclude_from_nav=True)

    print('parsing ' + found_url)
    resp = requests.get(found_url)
    dom = fromstring(resp.content)
    try:
        title = unidecode(dom.cssselect('h1')[0].text_content())
    except IndexError:
        print('bad url: ' + found_url)
        continue
    _id = normalizer.normalize(found_url.split('/')[-1])
    if _id in container.objectIds():
        continue
    kw = {}
    imgs = dom.cssselect('#mw-content-text img')
    if len(imgs) > 0:
        im_url = imgs[0].attrib['src']
        if im_url.startswith('//'):
            im_url = 'https:' + im_url
        resp = requests.get(im_url)
        kw['image'] = NamedBlobImage(
            data=resp.content,
            filename=unidecode(im_url.split('/')[-1]).decode('utf8'))
    obj = api.content.create(type='Document', id=_id, title=title,
                             exclude_from_nav=True, container=container, **kw)
    text = ''
    for p in dom.cssselect('#mw-content-text p'):
        text += tostring(p)
    bdata = IRichText(obj, None)
    bdata.text = RichTextValue(text, 'text/html', 'text/html')

    obj.reindexObject()

    parsed.append(found_url)

transaction.commit()
