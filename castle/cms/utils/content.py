import logging
import os
import types
from urllib import unquote

import transaction
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms.constants import MAX_PASTE_ITEMS
from castle.cms.interfaces import IHasDefaultImage
from castle.cms.interfaces import IReferenceNamedImage
from OFS.CopySupport import CopyError
from OFS.CopySupport import _cb_decode
from OFS.CopySupport import eInvalid
from plone import api
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.contentlisting.interfaces import IContentListingObject
from plone.app.uuid.utils import uuidToCatalogBrain
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityEditForm
from plone.subrequest import subrequest
from ZODB.POSException import POSKeyError


logger = logging.getLogger('castle.cms')


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


def clear_object_cache(ob):
    ob._p_jar.invalidateCache()
    transaction.begin()
    ob._p_jar.sync()


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


def get_object_version(obj, version):
    context = aq_inner(obj)
    if version == "current":
        return context
    else:
        repo_tool = api.portal.get_tool('portal_repository')
        return repo_tool.retrieve(context, int(version)).object


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


def get_context_from_request(request):
    published = request.get('PUBLISHED')
    if isinstance(published, types.MethodType):
        return published.im_self
    return aq_parent(published)


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
