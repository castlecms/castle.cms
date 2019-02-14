import argparse
import datetime
import logging

import requests

from castle.cms.cron.utils import login_as_admin
from castle.cms.cron.utils import setup_site
from castle.cms.utils import clear_object_cache
from plone.app.blocks import tiles
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.utils import getLayout
from plone.app.uuid.utils import uuidToCatalogBrain
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from repoze.xmliter.utils import getHTMLSerializer
from unidecode import unidecode
from zope.globalrequest import getRequest


logger = logging.getLogger(__name__)


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Castle')
args, _ = parser.parse_known_args()


class BadResponse(object):
    status_code = 500


_safe = [
    'https://twitter.com/intent/tweet',
    'https://www.facebook.com/sharer/sharer.php',
    'http://www.addthis.com',
    'javascript:'
]

_known_bad = [
    'http://www.captcha.net',
    'https://elements.psu.edu',
    'https://supervisord.org',
]


def find_url(ob, url):

    for bad in _known_bad:
        if url.startswith(bad):
            return False

    for safe in _safe:
        if safe in url:
            return True

    if 'resolveuid/' in url:
        # check if object...
        uid = url.split('resolveuid/')[-1]
        uid = uid.split('/')[0]
        return uuidToCatalogBrain(uid) is not None
    elif (('https://' in url or 'http://' in url) and
            'http://nohost' not in url):
        try:
            print('checking ' + url)
            resp = requests.get(url, stream=True, timeout=5)
        except Exception:
            resp = BadResponse()
        return resp.status_code == 200
    else:
        if 'http://nohost' in url:
            url = url.replace('http://nohost', '')
        url = url.replace('%20', ' ').split(
            '?')[0].split('#')[0].split('/@@images')[0]
        try:
            return ob.restrictedTraverse(str(url), None) is not None
        except Exception:
            return False


def find_broken(site):
    setup_site(site)
    catalog = site.portal_catalog

    broken = []
    good_urls = []
    checked_urls = []

    req = getRequest()
    for brain in catalog(object_provides=ILayoutAware.__identifier__):
        ob = brain.getObject()
        clear_object_cache(ob)
        layout = getLayout(ob)
        dom = getHTMLSerializer(layout)
        tiles.renderTiles(req, dom.tree, ob.absolute_url() + '/layout_view')
        root = dom.tree.getroot()
        for anchor in root.cssselect('a'):
            if not anchor.attrib.get('href'):
                continue
            url = anchor.attrib['href']
            if (url[0] == '#' or url.startswith('data:') or
                    url.startswith('mailto:')):
                continue
            if url in good_urls:
                continue
            if url in checked_urls:
                print('skipping already checked {}'.format(url))
                continue
            checked_urls.append(url)
            if find_url(ob, url):
                good_urls.append(url)
            else:
                try:
                    text = unidecode(anchor.text_content())
                except Exception:
                    text = ''
                result = '{} linking to broken -> {}({})'.format(
                    brain.getPath(),
                    url,
                    text
                )
                broken.append(result)
                print(result)

        for img in root.cssselect('img'):
            if not img.attrib.get('src'):
                continue
            url = img.attrib['src']
            if url[0] == '#' or url.startswith('data:'):
                continue
            if url in checked_urls:
                print('skipping already checked {}'.format(url))
                continue
            checked_urls.append(url)
            if find_url(ob, url):
                good_urls.append(url)
            else:
                result = '{} linking to broken image -> {}'.format(
                    brain.getPath(),
                    url
                )
                broken.append(result)
                print(result)

    now = datetime.datetime.now()
    filename = 'broken-links-{}.txt'.format(now.isoformat())
    fi = open(filename, 'w')
    fi.write('\n'.join(broken))
    fi.close()


if __name__ == '__main__':
    login_as_admin(app)  # noqa
    site = app[args.site_id]  # noqa
    if IPloneSiteRoot.providedBy(site):
        try:
            find_broken(site)
        except Exception:
            logger.error('Encountered error %s' % site, exc_info=True)
    else:
        logger.error('%s is not a site' % site)
