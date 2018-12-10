from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from BTrees.OOBTree import OOBTree
from castle.cms import cache
from castle.cms.constants import ALL_SUBSCRIBERS
from castle.cms.constants import ALL_USERS
from castle.cms.constants import MAX_PASTE_ITEMS
from castle.cms.interfaces import IHasDefaultImage
from castle.cms.interfaces import IReferenceNamedImage
from collective.elasticsearch.es import ElasticSearchCatalog
from collective.elasticsearch.hook import index_batch
from collective.elasticsearch.interfaces import IElasticSettings
from DateTime import DateTime
from datetime import datetime
from elasticsearch import Elasticsearch
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha256 as sha
from html2text import html2text
from lxml.html import fromstring
from lxml.html import tostring
from lxml.html.clean import Cleaner
from OFS.CopySupport import _cb_decode
from OFS.CopySupport import CopyError
from OFS.CopySupport import eInvalid
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from plone import api
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.app.querystring import queryparser
from plone.app.querystring.interfaces import IParsedQueryIndexModifier
from plone.app.uuid.utils import uuidToCatalogBrain
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityEditForm
from plone.registry.interfaces import IRegistry
from plone.subrequest import subrequest
from plone.uuid.interfaces import IUUID
from Products.CMFPlone.interfaces.controlpanel import IMailSchema
from urllib import unquote
from ZODB.POSException import ConflictError
from ZODB.POSException import POSKeyError
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.component import queryUtility
from zope.globalrequest import getRequest
from zope.security.interfaces import IPermission

import hashlib
import json
import logging
import os
import random
import re
import requests
import time
import transaction
import types


try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:

    using_sysrandom = False

SECRET = random.randint(0, 1000000)
logger = logging.getLogger('castle.cms')
ANONYMOUS_USER = "Anonymous User"


_truncate_cleaner = Cleaner(
    scripts=True, javascript=True, comments=True, style=True, links=True,
    meta=True, page_structure=True, embedded=True, frames=True, forms=True,
    annoying_tags=True, remove_tags=('div',), kill_tags=('img', 'hr'),
    remove_unknown_tags=True)


def truncate_text(text, max_words=30, more_link=None, clean=False):
    """
    adapted from Django
    """

    if not isinstance(text, basestring):
        return ''

    if clean:
        try:
            if not isinstance(text, unicode):
                text = text.decode('utf8')
            xml = fromstring(text)
            _truncate_cleaner(xml)
            # also remove empty tags...
            for p in xml.xpath("//p"):
                if len(p):
                    continue
                t = p.text
                if not (t and t.replace('&nbsp;', '').strip()):
                    p.getparent().remove(p)
            text = tostring(xml)
        except Exception:
            pass
    length = int(max_words)
    if length <= 0:
        return u''
    html4_singlets = ('br', 'col', 'link', 'base',
                      'img', 'param', 'area', 'hr', 'input')
    # Set up regular expressions
    re_words = re.compile(r'&.*?;|<.*?>|(\w[\w-]*)', re.U)
    re_tag = re.compile(r'<(/)?([^ ]+?)(?: (/)| .*?)?>')
    # Count non-HTML words and keep note of open tags
    pos = 0
    end_text_pos = 0
    words = 0
    open_tags = []
    while words <= length:
        m = re_words.search(text, pos)
        if not m:
            # Checked through whole string
            break
        pos = m.end(0)
        if m.group(1):
            # It's an actual non-HTML word
            words += 1
            if words == length:
                end_text_pos = pos
            continue
        # Check for tag
        tag = re_tag.match(m.group(0))
        if not tag or end_text_pos:
            # Don't worry about non tags or tags after our truncate point
            continue
        closing_tag, tagname, self_closing = tag.groups()
        tagname = tagname.lower()  # Element names are always case-insensitive
        if self_closing or tagname in html4_singlets:
            pass
        elif closing_tag:
            # Check for match in open tags list
            try:
                i = open_tags.index(tagname)
            except ValueError:
                pass
            else:
                # SGML: An end tag closes, back to the matching start tag,
                # all unclosed intervening start tags with omitted end tags
                open_tags = open_tags[i + 1:]
        else:
            # Add it to the start of the open tags list
            open_tags.insert(0, tagname)

    if words <= length:
        # Don't try to close tags if we don't need to truncate
        return text
    out = text[:end_text_pos]
    out += '&hellip;'
    if more_link:
        out += ' <a href="%s">more &#x2192;</a>' % more_link
    # Close any tags still open
    for tag in open_tags:
        out += '</%s>' % tag
    # Return string
    return out


truncateText = truncate_text


def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    Returns a securely generated random string.

    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(
            sha(
                "%s%s%s" % (
                    random.getstate(),
                    time.time(),
                    SECRET)
                ).digest())  # noqa
    return ''.join([random.choice(allowed_chars) for i in range(length)])


def make_random_key(length=150, prefix=''):
    if prefix:
        prefix = str(prefix) + '-'
    hashed = '%s%s' % (
        hashlib.sha1(str(get_random_string(length)).encode('utf-8')).hexdigest()[:5],  # noqa
        str(datetime.now().microsecond)
    )
    return prefix + hashlib.sha1(hashed.encode('utf-8')).hexdigest()[:length]


def get_paste_data(req):
    try:
        op, mdatas = _cb_decode(req['__cp'])
    except Exception:
        raise CopyError(eInvalid)

    try:
        if mdatas[0][0].startswith('cache:'):
            cache_key = mdatas[0][0].replace('cache:', '')
            mdatas = cache.get(cache_key)
    except IndexError:
        pass

    paths = []
    for mdata in mdatas:
        paths.append('/'.join(mdata))

    catalog = api.portal.get_tool('portal_catalog')
    count = len(catalog(path={'query': paths, 'depth': -1}))

    return {
        'paths': paths,
        'op': op,
        'mdatas': mdatas,
        'count': count
    }


def is_max_paste_items(paste_data):
    return paste_data['count'] > MAX_PASTE_ITEMS


def recursive_create_path(site, path):
    if path == '/':
        folder = site
    else:
        path = path.lstrip('/')
        folder = site.restrictedTraverse(path, None)
        if folder is None:
            # Need to create folders up to where we want content
            # we'll walk it up create folders as needed
            folder = site
            for part in path.split('/'):
                try:
                    folder = folder[part]
                except KeyError:
                    folder = api.content.create(
                        type='Folder',
                        id=part,
                        title=part.capitalize().replace('-', ' '),
                        container=folder)
    return folder


def retriable(count=3, sync=False, reraise=True, on_retry_exhausted=None):

    def decorator(func):
        def wrapped(*args, **kwargs):
            retried = 0
            if sync:
                try:
                    api.portal.get()._p_jar.sync()
                except Exception:
                    pass
            while retried < count:
                try:
                    return func(*args, **kwargs)
                except ConflictError:
                    retried += 1
                    try:
                        api.portal.get()._p_jar.sync()
                    except Exception:
                        if retried >= count:
                            if on_retry_exhausted is not None:
                                on_retry_exhausted(*args, **kwargs)
                            if reraise:
                                raise
        return wrapped
    return decorator


def clear_object_cache(ob):
    ob._p_jar.invalidateCache()
    transaction.begin()
    ob._p_jar.sync()


def index_in_es(obj):
    catalog = api.portal.get_tool('portal_catalog')
    es = ElasticSearchCatalog(catalog)
    if es.enabled:
        index_batch([], {IUUID(obj): obj}, [], es)


def verify_recaptcha(req=None):
    if req is None:
        req = getRequest()

    registry = getUtility(IRegistry)
    key = registry.get('castle.recaptcha_private_key', '')
    if not key:
        # do not bother verifying if no key is defined
        return True
    code = req.form.get('g-recaptcha-response', '')
    remote_addr = req.get(
        'HTTP_X_FORWARDED_FOR',
        ''
    ).split(',')[0]
    if not remote_addr:
        remote_addr = req.get('REMOTE_ADDR')

    resp = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data=dict(
            secret=key,
            response=code,
            remoteip=remote_addr
        )
    )
    try:
        return resp.json()['success']
    except Exception:
        return False


def get_email_from_address():
    registry = getUtility(IRegistry)
    mail_settings = registry.forInterface(IMailSchema, prefix='plone')
    return mail_settings.email_from_address


def send_email(recipients=None, subject=None, html='', text='', sender=None):
    if isinstance(recipients, basestring):
        recipients = [recipients]

    cleaned_recipients = []
    for recipient in recipients:
        if recipients == ALL_USERS:
            for user in api.user.get_users():
                email = user.getProperty('email')
                if email:
                    cleaned_recipients.append(email)
        elif recipients == ALL_SUBSCRIBERS:
            from castle.cms import subscribe
            cleaned_recipients.extend(subscribe.get_email_addresses())
        else:
            cleaned_recipients.append(recipient)

    if sender is None:
        sender = get_email_from_address()

    if not text and html:
        try:
            text = html2text(html)
        except Exception:
            pass

    for recipient in cleaned_recipients:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        if text:
            part = MIMEText(text, 'plain')
            msg.attach(part)
        if html:
            part = MIMEText(html, 'html')
            msg.attach(part)

        mailhost = api.portal.get_tool('MailHost')
        mailhost.send(msg.as_string())


def inline_images_in_dom(dom, portal=None, site_url=None):
    if portal is None:
        portal = api.portal.get()
    if site_url is None:
        site_url = portal.absolute_url()
    for img in dom.cssselect('img'):
        src = img.attrib.get('src', '')
        if src.startswith(site_url):
            ctype, data = get_data_from_url(src, portal, site_url)
            if not ctype or not data or 'image' not in ctype:
                img.attrib['src'] = ''
                continue
            data = data.encode("base64").replace("\n", "")
            data_uri = 'data:{0};base64,{1}'.format(ctype, data)
            img.attrib['src'] = data_uri


def ESConnectionFactoryFactory(registry=None):
    if registry is None:
        registry = getUtility(IRegistry)
    settings = registry.forInterface(IElasticSettings, check=False)
    hosts = settings.hosts
    opts = dict(
        timeout=getattr(settings, 'timeout', 0.5),
        sniff_on_start=getattr(settings, 'sniff_on_start', False),
        sniff_on_connection_fail=getattr(
            settings, 'sniff_on_connection_fail', False),
        sniffer_timeout=getattr(settings, 'sniffer_timeout', 0.1),
        retry_on_timeout=getattr(settings, 'retry_on_timeout', False)
    )

    def factory():
        return Elasticsearch(hosts, **opts)
    return factory


def add_indexes(indexes):
    """
    indexes should be a tuple of (name of the index, index type)
    """
    catalog = api.portal.get_tool('portal_catalog')
    for name, _type in indexes.items():
        if name not in catalog.indexes():
            if type(_type) == dict:
                real_type = _type['type']
                del _type['type']
                catalog.addIndex(name, real_type, **_type)
            else:
                catalog.addIndex(name, _type)


def delete_indexes(indexes):
    catalog = api.portal.get_tool('portal_catalog')
    for name in indexes:
        if name in catalog.indexes():
            catalog.delIndex(name)


def add_metadata(metadata):
    catalog = api.portal.get_tool('portal_catalog')
    _catalog = catalog._catalog
    for name in metadata:
        if name not in catalog.schema():
            # override how this works normally to not cause a reindex
            schema = _catalog.schema
            names = list(_catalog.names)
            values = schema.values()
            if values:
                schema[name] = max(values) + 1
            else:
                schema[name] = 0
            names.append(name)

            _catalog.names = tuple(names)
            _catalog.schema = schema


def delete_metadata(metadata):
    catalog = api.portal.get_tool('portal_catalog')
    for name in metadata:
        if name in catalog.schema():
            catalog.delColumn(name)


def is_mosaic_edit_form(request):
    try:
        if (ILayoutAware.providedBy(request.PUBLISHED.context) and
                IDexterityEditForm.providedBy(request.PUBLISHED) and
                request.PUBLISHED.context.getLayout() == 'layout_view' and
                request.PUBLISHED.__name__ == 'edit'):
            return True
    except Exception:
        pass
    return False


def get_ip(req):
    ip = req.get('HTTP_CF_CONNECTING_IP')
    if not ip:
        ip = req.get('HTTP_X_FORWARDED_FOR')
    if not ip:
        ip = req.get('HTTP_X_REAL_IP')
    if not ip:
        ip = req.get('REMOTE_ADDR')
    return ip


def get_backend_url():
    registry = getUtility(IRegistry)
    backend_url = registry.get('plone.backend_url', None)
    if not backend_url or len(backend_url) == 0:
        return api.portal.get().absolute_url()
    else:
        return backend_url[0]


def no_backend_url(value):
    try:
        url = str(value)
        backend = get_backend_url()
        if backend in url:
            return False
        return True
    except Exception:
        return True


def parse_query_from_data(data, context=None):
    if context is None:
        context = api.portal.get()
    query = data.get('query', {}) or {}
    try:
        parsed = queryparser.parseFormquery(context, query)
    except KeyError:
        logger.info('Error parsing query {}'.format(repr(query)))
        parsed = {}

    index_modifiers = getUtilitiesFor(IParsedQueryIndexModifier)
    for name, modifier in index_modifiers:
        if name in parsed:
            new_name, query = modifier(parsed[name])
            parsed[name] = query
            # if a new index name has been returned, we need to replace
            # the native ones
            if name != new_name:
                del parsed[name]
                parsed[new_name] = query

    if data.get('sort_on'):
        parsed['sort_on'] = data['sort_on']
    if data.get('sort_reversed', False):
        parsed['sort_order'] = 'reverse'
    return parsed


def normalize_url(url):
    url = url.split('#')[0]
    if url.startswith('data:'):
        return None
    return url


def strings_differ(string1, string2):
    """Check whether two strings differ while avoiding timing attacks.

    This function returns True if the given strings differ and False
    if they are equal.  It's careful not to leak information about *where*
    they differ as a result of its running time, which can be very important
    to avoid certain timing-related crypto attacks:

        http://seb.dbzteam.org/crypto/python-oauth-timing-hmac.pdf

    """
    if len(string1) != len(string2):
        return True

    invalid_bits = 0
    for a, b in zip(string1, string2):
        invalid_bits += a != b

    return invalid_bits != 0


def get_public_url():
    public_url = api.portal.get_registry_record('plone.public_url')
    if not public_url:
        public_url = api.portal.get().absolute_url()
    return public_url


def get_object_version(obj, version):
    context = aq_inner(obj)
    if version == "current":
        return context
    else:
        repo_tool = api.portal.get_tool('portal_repository')
        return repo_tool.retrieve(context, int(version)).object


def _customhandler(obj):
    if type(obj) == DateTime:
        return obj.ISO8601()
    if type(obj) == PersistentList:
        return list(obj)
    if type(obj) == PersistentDict:
        return dict(obj)
    if type(obj) == OOBTree:
        return dict(obj)
    raise TypeError(
        "Unserializable object {} of type {}".format(obj, type(obj)))


def json_dumps(data):
    return json.dumps(data, default=_customhandler)


def get_path(obj, site=None):
    """
    Get the full path FROM the site of an object
    path object: /Castle/foo/bar -> /foo/bar
    """
    if site is None:
        site = api.portal.get()
    site_path = site.getPhysicalPath()
    obj_path = obj.getPhysicalPath()
    path = '/' + '/'.join(obj_path[len(site_path):])
    return path


def get_data_from_url(url, portal=None, site_url=None):
    if portal is None:
        portal = api.portal.get()
    if site_url is None:
        site_url = portal.absolute_url()
    data = None
    path = url.replace(site_url, '').strip('/')
    ct = ''
    if '/@@images/' in path:
        try:
            path, _, im_info = path.partition('/@@images/')
            parts = im_info.split('/')
            if len(parts) == 2:
                fieldname = parts[0]
                size = parts[1]
                images = portal.restrictedTraverse(
                    str(path + '/@@images'), None)
                if images is not None:
                    im = images.traverse(fieldname, [size])
                    try:
                        data = im.scale.data.data
                        ct = im.scale.data.contentType
                    except AttributeError:
                        pass
            else:
                # grab full size
                ob = portal.restrictedTraverse(str(path), None)
                data = ob.image.data
                ct = ob.image.contentType
        except Exception:
            logger.error('Could not traverse image ' + url, exc_info=True)

    if data is None:
        ob = portal.restrictedTraverse(str(path), None)
        file_path = getattr(ob, 'path', None)
        if file_path is None:
            try:
                file_path = ob.context.path
            except Exception:
                pass
        if file_path and os.path.exists(file_path):
            fi = open(file_path)
            data = fi.read()
            fi.close()
            ct = 'image/' + file_path.split('.')[-1].lower()
        else:
            resp = subrequest(unquote(url))
            if resp.status != 200:
                return None, None
            try:
                ct, encoding = resp.getHeader(
                    'content-type').split('charset=')
                ct = ct.split(';')[0]
                # pisa only likes ascii css
                data = resp.getBody().decode(encoding)
            except ValueError:
                ct = resp.getHeader('content-type').split(';')[0]
                data = resp.getBody()

    return ct, data


def get_image_info(brain):
    image_info = None
    if IContentListingObject.providedBy(brain):
        brain = brain._brain
    if IDexterityContent.providedBy(brain):
        obj = brain
        try:
            image = obj.image
            if IReferenceNamedImage.providedBy(image):
                uid = image.reference
                brain = uuidToCatalogBrain(uid)
                if brain:
                    return get_image_info(brain)
                else:
                    return
            width, height = image.getImageSize()
            image_info = {
                'width': width,
                'height': height
            }
            try:
                image_info['focal_point'] = image.focal_point
            except Exception:
                try:
                    image_info['focal_point'] = obj._image_focal_point
                except Exception:
                    image_info['focal_point'] = [width / 2, height / 2]
        except AttributeError:
            pass
    else:
        try:
            image_info = brain.image_info
            if 'reference' in image_info:
                uid = image_info['reference']
                brain = uuidToCatalogBrain(uid)
                if brain:
                    return get_image_info(brain)
        except Exception:
            pass

    return image_info


def get_folder_contents(folder, **query):
    query.update({
        'sort_on': 'getObjPositionInParent',
        'path': {
            'query': '/'.join(folder.getPhysicalPath()),
            'depth': 1
        },
        'show_inactive': False
    })
    catalog = api.portal.get_tool('portal_catalog')
    return catalog(**query)


def site_has_icon():
    key = '{}.has_site_icon'.format(
        ''.join(api.portal.get().getPhysicalPath()))
    try:
        has_icon = cache.ram.get(key)
    except KeyError:
        registry = getUtility(IRegistry)
        has_icon = False
        try:
            has_icon = bool(registry['plone.site_icon'])
        except Exception:
            pass
        cache.ram.set(key, has_icon)
    return has_icon


def get_context_from_request(request):
    published = request.get('PUBLISHED')
    if isinstance(published, types.MethodType):
        return published.im_self
    return aq_parent(published)


def get_managers():
    managers = []
    for admin_user in api.user.get_users():
        user_roles = api.user.get_roles(user=admin_user)
        admin_email = admin_user.getProperty('email')
        if (('Manager' not in user_roles and
                'Site Administrator' not in user_roles) or
                not admin_email):
            continue
        managers.append(admin_user)
    return managers


def has_image(obj):
    try:
        # check if brain has the data
        return obj.hasImage
    except Exception:
        if getattr(obj, 'getObject', False):
            obj = obj.getObject()
        if IHasDefaultImage.providedBy(obj):
            return True
        try:
            return getattr(aq_base(obj), 'image', None) is not None
        except POSKeyError:
            return False


def get_permission_title(permission):
    add_perm_ob = queryUtility(IPermission, name=permission)
    if add_perm_ob:
        permission = add_perm_ob.title
    return permission


def publish_content(obj):
    try:
        api.content.transition(obj=obj, transition='publish')
    except api.exc.InvalidParameterError:
        try:
            api.content.transition(obj=obj, transition='publish_internally')
        except api.exc.InvalidParameterError:
            # not a valid transition, move on I guess...
            pass


def get_upload_fields(registry=None):
    if registry is None:
        registry = getUtility(IRegistry)
    upload_fields = registry.get('castle.file_upload_fields', None)
    if upload_fields is None:
        # not updated yet, b/w compatiable
        required_upload_fields = registry.get(
            'castle.required_file_upload_fields', []) or []
        result = [{
            'name': 'title',
            'label': 'Title',
            'widget': 'text',
            'required': 'title' in required_upload_fields,
            'for-file-types': '*'
        }, {
            'name': 'description',
            'label': 'Summary',
            'widget': 'textarea',
            'required': 'description' in required_upload_fields,
            'for-file-types': '*'
        }, {
            'name': 'tags',
            'label': 'Tags',
            'widget': 'tags',
            'required': 'tags' in required_upload_fields,
            'for-file-types': '*'
        }, {
            'name': 'youtube_url',
            'label': 'Youtube URL',
            'widget': 'text',
            'required': 'youtube_url' in required_upload_fields,
            'for-file-types': 'video'
        }]
    else:
        result = []
        for field in upload_fields:
            if 'name' not in field:
                continue
            # need to make copy of data otherwise we're potentially
            # modifying the record directly
            data = {}
            data.update(field)
            # make sure all required field are in place
            if data.get('required'):
                data['required'] = str(data['required']).lower() in ('true', 't', '1')
            else:
                data['required'] = False
            if 'label' not in data:
                data[u'label'] = data[u'name'].capitalize()
            if 'widget' not in field:
                data[u'widget'] = u'text'
            if 'for-file-types' not in data:
                data[u'for-file-types'] = u'*'
            result.append(data)
    return result
