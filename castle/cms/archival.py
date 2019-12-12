# for compat with python3, specifically the urllib.parse includes
# noqa because these need to precede other imports
from future.standard_library import install_aliases
install_aliases()  # noqa

from BTrees.OOBTree import OOBTree
from castle.cms import theming
from castle.cms.files import aws
from castle.cms.interfaces import IArchiveContentTransformer, IArchiveManager
from castle.cms.utils import normalize_url
from DateTime import DateTime
from lxml.html import fromstring
from lxml.html import tostring
from plone import api
from plone.subrequest import subrequest
from plone.uuid.interfaces import IUUID
from urllib.parse import urlparse, urljoin, quote_plus
from zope.component import getAllUtilitiesRegisteredFor
from zope.globalrequest import getRequest
from zope.interface import implements

import hashlib
import logging
import re
import requests


logger = logging.getLogger('castle.cms')


# gets all url() CSS directives
RE_CSS_URL = re.compile(r"""url\(["']?([^\)'"]+)['"]?\)""")
# inline css import...
RE_CSS_IMPORTS = re.compile(r"""\@import ["']([a-zA-Z0-9\+\.\-\/\:\_]+\.(?:css))["'];""")  # noqa

CONTENT_KEY_PREFIX = 'archives/'
RESOURCES_KEY_PREFIX = 'archiveresources/'


class BaseArchivalTransformer(object):
    implements(IArchiveContentTransformer)

    def __init__(self, archiver):
        self.archiver = archiver

    def __call__(dom):
        pass


class ArchiveManager(object):

    implements(IArchiveManager)

    def getContentToArchive(self, delta=0):
        days = api.portal.get_registry_record(
            'castle.archival_number_of_days') - delta
        types = api.portal.get_registry_record(
            'castle.archival_types_to_archive')
        states = api.portal.get_registry_record(
            'castle.archival_states_to_archive')
        if not types or not states:
            return []
        catalog = api.portal.get_tool('portal_catalog')
        end = DateTime()
        if days > 0:
            end -= days  # we're looking for data last modified
        query = dict(
            portal_type=types,
            modified={
                'query': (DateTime('1999/09/09'), end),
                'range': 'min:max'
            },
            sort_on="modified",
            review_state=states)
        return catalog(**query)


class ImageResourceMover(object):
    keep_ext = False

    attr = 'src'
    selector = 'img'

    def __init__(self, dom):
        self.dom = dom

    def get_elements(self):
        return self.dom.cssselect(self.selector)

    def get_url(self, el):
        return el.attrib.get(self.attr)

    def modify(self, el, new_url):
        el.attrib['original-url'] = el.attrib[self.attr]
        el.attrib[self.attr] = new_url


class LinkResourceMover(ImageResourceMover):
    attr = 'href'
    selector = 'link[rel="stylesheet"]'


class StyleResourceMover(ImageResourceMover):
    selector = 'style[type="text/css"]'

    def get_url(self, el):
        if not el.text:
            return
        if not el.text.startswith('@import'):
            return None
        return el.text.strip().lstrip('@import url(').rstrip(');')

    def modify(self, el, new_url):
        el.text = el.text.replace(self.get_url(el), new_url)


class ScriptResourceMover(ImageResourceMover):
    attr = 'src'
    selector = 'script[src]'


class EmbedResourceMover(ImageResourceMover):
    attr = 'src'
    selector = 'embed[src]'


class ObjectResourceMover(ImageResourceMover):
    attr = 'data'
    selector = 'object[data]'


class FlashScriptResourceMover(ImageResourceMover):
    """
    Example:
    <script type="text/javascript">
AC_FL_RunContent('codebase','http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,28,0','width','920','height','670','src','foobar','quality','high','wmode','transparent','pluginspage','http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash','movie','foobar' );
</script>
    """  # noqa

    keep_ext = True

    def get_elements(self):
        results = []
        for script in self.dom.cssselect('script'):
            if 'src' in script.attrib:
                continue
            if 'AC_FL_RunContent' in script.text:
                results.append(script)
        return results

    def get_rel_url(self, el):
        script = None
        for line in el.text.strip().splitlines():
            line = line.strip()
            if line.startswith('//'):
                continue
            if ' //' in line:
                line = line.split(' //')[0]
            if 'AC_FL_RunContent' in line:
                script = line
                break
        if script:
            params = script.replace('AC_FL_RunContent(', '').replace(');', '').split(',')  # noqa
            swf = params[-1].replace('"', '').replace("'", '').strip()
            return swf

    def get_url(self, el):
        swf = self.get_rel_url(el)

        if not swf:
            return

        swf = swf.split('?')[0]

        if not swf.lower().endswith('.swf'):
            swf += '.swf'

        # if relative use base tag...
        if swf[0] == '/' or 'https://' in swf or 'http://' in swf:
            return swf

        base = self.dom.cssselect('base[href]')
        if len(base) > 0:
            swf = urljoin(base[0].attrib['href'], swf)
        else:
            body = self.dom.cssselect('body')[0]
            if 'data-portal-url' in body.attrib:
                swf = urljoin(body.attrib['data-portal-url'], swf)
        return swf

    def modify(self, el, new_url):
        swf = self.get_rel_url(el)
        el.text = el.text.replace(swf, new_url.replace('.swf', ''))


def _get_vhm_base_url(public_url, site_path):
    if not public_url:
        return site_path
    parsed = urlparse(public_url)
    return '/VirtualHostBase/%s/%s:%i%s/VirtualHostRoot' % (
        parsed.scheme,
        parsed.netloc,
        parsed.scheme == 'http' and 80 or 443,
        site_path
    )


class RequestsUrlOpener(object):
    def __init__(self, migrator):
        self.migrator = migrator
        self.site = migrator.site

    def __call__(self, url):
        url = normalize_url(url)
        if not url:
            return

        resp = requests.get(url)
        if resp.status_code in (404, 403, 401, 500, 501, 502):
            return
        if len(resp.history) > 0:
            # if it was a redirect and came_from in the url
            if (resp.history[-1].status_code in (301, 302) and
                    'came_from' in resp.url):
                return

        return {
            'data': resp.content,
            'headers': resp.headers,
            'code': resp.status_code
        }


class SubrequestUrlOpener(object):
    _blacklisted_content = (
        '/refresh.png',
        '/contenttypes-sprite.png',
        '/glyphicons-halflings-regular.ttf',
        '/glyphicons-halflings-regular.svg',
        '/%23gradient',
        '/pb_close.png',
        '/delete.png',
        '/undelete.png',
        '/event_icon.png',
        '/++resource++plone.app.jquerytools.next.gif',
        '/++resource++plone.app.jquerytools.prev.gif',
        '/++resource++plone.app.jquerytools.pb_close.png',
        '/popup_calendar.png',
        '/next.gif',
        '/prev.gif'
    )

    def __init__(self, migrator):
        self.migrator = migrator
        self.site = migrator.site
        self.site_path = '/'.join(self.site.getPhysicalPath())
        self.public_url = api.portal.get_registry_record('plone.public_url')
        if not self.public_url:
            self.public_url = self.site.absolute_url()
        self.vhm_base = _get_vhm_base_url(self.public_url, self.site_path)

    def __call__(self, url, use_vhm=True):
        url = normalize_url(url)
        if not url:
            return

        if not url.startswith(self.public_url):
            return

        if '++plone++production' in url:
            front, end = url.rsplit('/', 1)
            # check blacklist
            for black_listed in self._blacklisted_content:
                if url.startswith(front + black_listed):
                    return

        # since we're looking at plone here... let's try fixing up urls...
        if '++plone++' in url:
            # can always be from site root
            url = self.public_url + '/++plone++' + url.rsplit('++plone++', 1)[-1]  # noqa

        if use_vhm:
            parsed = urlparse(url)
            vhm_path = self.vhm_base + parsed.path
            resp = subrequest(vhm_path)
        else:
            resp = subrequest(url)
        if resp.getStatus() == 404:
            return

        return {
            'data': resp.getBody(),
            'headers': resp.headers,
            'code': resp.getStatus()
        }


class Storage(object):
    """
    We store data on content we've moved:
        1) new url in AWS
        2) UID of obj we moved -> for resolveuid issues
        3) path of obj -> for regular 404s
    """

    Movers = (
        ImageResourceMover,
        LinkResourceMover,
        StyleResourceMover,
        ScriptResourceMover,
        FlashScriptResourceMover,
        ObjectResourceMover,
        EmbedResourceMover
    )
    _s3_conn = _bucket = None

    def __init__(self, site, UrlOpener=SubrequestUrlOpener):
        self.site = site
        self.url_opener = UrlOpener(self)
        self.public_url = api.portal.get_registry_record('plone.public_url')
        try:
            self.archives = self.site._archives
            self.path_to_uid = self.site._archives_path_to_uid
        except AttributeError:
            self.archives = self.site._archives = OOBTree()
            self.path_to_uid = self.site._archives_path_to_uid = OOBTree()
        self.resources = {}  # path -> md5 dict
        self.errors = []  # so we can ignore

        try:
            self.replacements = api.portal.get_registry_record(
                'castle.archival_replacements') or {}
        except Exception:
            self.replacements = {}

        self.view_url_types = api.portal.get_registry_record(
            'plone.types_use_view_action_in_listings')

    @property
    def s3_conn(self):
        if self._s3_conn is None:
            self._initialize_s3()
        return self._s3_conn

    @property
    def bucket(self):
        if self._bucket is None:
            self._initialize_s3()
        return self._bucket

    def _initialize_s3(self):
        bucket_name = api.portal.get_registry_record(
            'castle.aws_s3_bucket_name')
        self._s3_conn, self._bucket = aws.get_bucket(s3_bucket=bucket_name)

    def apply_replacements(self, content):
        # first pass is for straight text
        for key, val in self.replacements.items():
            if key[0] == '.' or key[1] == '#':
                continue
            content = content.replace(key, val)

        dom = fromstring(content)
        for key, val in self.replacements.items():
            if key[0] != '.' and key[1] != '#':
                continue
            el = dom.cssselect(key)
            if len(el) > 0:
                el[0].text = val
                if 'style' in el[0].attrib:
                    del el[0].attrib['style']
                # also check parent
                parent = el[0].getparent()
                if 'style' in parent.attrib:
                    del parent.attrib['style']

        return tostring(dom)

    def move_to_aws(self, content, content_path,
                    content_type='text/html; charset=utf-8'):
        # perform replacements
        if 'html' in content_type and self.replacements:
            content = self.apply_replacements(content)
        content_path = content_path.lstrip('/')
        content_path = CONTENT_KEY_PREFIX + content_path
        url = '{endpoint_url}/{bucket}/{key}'.format(
            endpoint_url=self.s3_conn.meta.client.meta.endpoint_url,
            bucket=self.bucket.name,
            key=quote_plus(content_path))

        aws.create_or_update(
            self.bucket,
            content_path,
            content_type,
            content)

        return url

    def move_resource(self, url, keep_ext=False, use_vhm=True):
        if 'data:' in url:
            return
        if url in self.errors:
            print('skipping because of error %s' % url)
            return
        resp = self.url_opener(url, use_vhm=use_vhm)
        if resp is None:
            self.errors.append(url)
            return
        logger.info('moving url: %s - %i' % (url, resp['code']))
        fidata = resp['data']

        # parse response, look for additional urls in content that need to be
        # moved over
        if 'text' in resp['headers'].get('content-type', '').lower():
            for sub_url in RE_CSS_URL.findall(fidata) + RE_CSS_IMPORTS.findall(fidata):
                resource_url = sub_url
                if not sub_url.startswith('http') and not sub_url.startswith('data:'):
                    resource_url = urljoin(url, sub_url)
                if resource_url not in self.resources:
                    moved_url = self.move_resource(resource_url)
                    if moved_url:
                        self.resources[resource_url] = moved_url
                if resource_url in self.resources:
                    new_url = self.resources[resource_url]
                    fidata = fidata.replace(sub_url, new_url)

        # upload to amazon and get url!
        md5 = hashlib.md5(fidata).hexdigest()

        content_path = '{0}{1}/{2}/{3}/{4}'.format(
            RESOURCES_KEY_PREFIX, md5[0], md5[1], md5[2], md5
        )
        if keep_ext and '.' in url:
            ext = url.split('.')[-1]
            content_path += '.' + ext
        new_url = '{endpoint_url}/{bucket}/{key}'.format(
            endpoint_url=self.s3_conn.meta.client.meta.endpoint_url,
            bucket=self.bucket.name,
            key=quote_plus(content_path))

        aws.create_if_not_exists(
            self.bucket,
            content_path,
            resp['headers']['content-type'],
            fidata,
            content_disposition=resp['headers'].get('content-disposition', None))

        return new_url

    def add_url(self, url, content_path, uid):
        resp = self.url_opener(url)
        if resp is None:
            return
        content = resp['data']
        if 'html' in resp['headers']['content-type']:
            content = self.transform_content(content, url)
        new_url = self.move_to_aws(content, content_path,
                                   content_type=resp['headers']['content-type'])
        self.archives[uid] = {
            'path': content_path,
            'url': new_url
        }
        self.path_to_uid[content_path] = uid
        return new_url

    def transform_content(self, content, from_url):
        parsed_url = urlparse(from_url)
        domain = parsed_url.netloc
        dom = fromstring(content)
        for Mover in self.Movers:
            mover = Mover(dom)
            for el in mover.get_elements():
                url = mover.get_url(el)
                if url is None:
                    continue

                if url[0] == '/':
                    url = '{}://{}{}'.format(parsed_url.scheme, domain, url)
                elif 'https://' not in url and 'http://' not in url:
                    url = urljoin(from_url, url)

                # check that the url is on the site...
                rdomain = urlparse(url).netloc
                if rdomain and domain != rdomain:
                    continue
                if url not in self.resources:
                    # need to move resource
                    resource_url = url
                    if not url.startswith('http'):
                        resource_url = urljoin(from_url, url)
                    moved_url = self.move_resource(resource_url, mover.keep_ext)
                    if moved_url:
                        self.resources[url] = moved_url
                if url in self.resources:
                    mover.modify(el, aws.swap_url(self.resources[url]))
        content = tostring(dom)
        for Util in getAllUtilitiesRegisteredFor(IArchiveContentTransformer):
            try:
                util = Util(self)
                content = util(content)
            except Exception:
                logger.info('Error with archive utility', exc_info=True)
        return content

    def massage_plone_resp_content(self, ob, resp, url):
        content = resp['data']
        if 'html' in resp['headers']['content-type']:
            if resp['headers'].get('x-theme-applied') != 'true':
                # annoying case where theme isn't applied here...

                req = getRequest()

                # XXX a bit weird, we need to virtualhostmonster it for transform...
                site_path = '/'.join(self.site.getPhysicalPath())
                public_url = api.portal.get_registry_record('plone.public_url')
                vhm_base = _get_vhm_base_url(public_url, site_path)
                req.traverse(vhm_base)

                transform = theming.getTransform(ob, req)
                content = ''.join(transform(req, content, context=ob))
            content = self.transform_content(content, url)
        return content

    def add_content(self, ob):
        site_path = '/'.join(self.site.getPhysicalPath())
        aws_content_path = content_path = '/'.join(ob.getPhysicalPath())[len(site_path):]

        uid = IUUID(ob)

        # first off, get url based off of public_url setting
        url = ob.absolute_url().replace(self.site.absolute_url(), self.public_url)

        resp = self.url_opener(url)
        if resp is None:
            return
        new_url = self.move_to_aws(self.massage_plone_resp_content(ob, resp, url),
                                   aws_content_path,
                                   content_type=resp['headers']['content-type'])

        view_url = None
        if ob.portal_type in self.view_url_types:
            aws_content_path += '/view'
            url += '/view'
            # first, download the regular url type for this content...
            resp = self.url_opener(url)
            if resp is not None:
                view_url = self.move_to_aws(self.massage_plone_resp_content(ob, resp, url),
                                            aws_content_path,
                                            content_type=resp['headers']['content-type'])

        self.archives[uid] = {
            'path': content_path,
            'url': new_url,
            'view_url_type': ob.portal_type in self.view_url_types,
            'view_url': view_url
        }
        self.path_to_uid[content_path] = uid
        return new_url

    def get_archive_url_by_uid(self, uid):
        return self.archives[uid]['url']

    def get_archive_url_by_path(self, path, wants_view=False):
        uid = self.path_to_uid[path]
        data = self.archives[uid]
        if wants_view:
            return data['view_url']
        else:
            return data['url']
