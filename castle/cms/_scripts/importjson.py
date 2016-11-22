from AccessControl.SecurityManagement import newSecurityManager
from castle.cms._scripts import mjson
from castle.cms._scripts.importtypes import getImportType
from lxml.html import fromstring
from lxml.html import tostring
from OFS.interfaces import IFolder
from plone import api
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.app.textfield.value import RichTextValue
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from zope.component import getUtility
from zope.component.hooks import setSite

import argparse
import logging
import os
import transaction


logger = logging.getLogger('castle.cms')

# ToDo:
#   - do NOT export images
#       - only images that are referenced in content
#   - lookup reference, if image only used once, add as lead image
#   - other images, if not referenced elsewhere, include inline
#       as data uris
#   - links that go to files should be moved to s3 and be converted
#       into file objects
#   - if default page and only page inside folder, replace folder
#


parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone')
parser.add_argument('--export-directory', dest='export_directory')
parser.add_argument('--overwrite', dest='overwrite', default=False)
args, _ = parser.parse_known_args()


user = app.acl_users.getUser('admin')  # noqa
newSecurityManager(None, user.__of__(app.acl_users))  # noqa
site = app[args.site_id]  # noqa
setSite(site)


def traverse(path):
    folder = site  # noqa
    for part in path.strip('/').split('/'):
        if part in folder.objectIds():
            folder = folder[part]
        else:
            return


def relpath(obj):
    return '/'.join(obj.getPhysicalPath())[len('/'.join(site.getPhysicalPath())) + 1:]


def recursive_create_path(path):
    if path in ('/', ''):
        folder = site
    else:
        path = path.lstrip('/')
        folder = traverse(path)
        if folder is not None and not IFolder.providedBy(folder):
            api.content.delete(folder)
            folder = None
        if folder is None:
            # Need to create folders up to where we want content
            # we'll walk it up create folders as needed
            folder = site
            for part in path.split('/'):
                try:
                    ob = folder[part]
                    if not IFolder.providedBy(ob):
                        api.content.delete(ob)
                        raise KeyError()
                    else:
                        folder = ob
                except (KeyError, AttributeError):
                    fpath = os.path.join(
                        args.export_directory,
                        relpath(folder),
                        part,
                        '__folder__')

                    if os.path.exists(fpath):
                        fi = open(fpath)
                        data = mjson.loads(fi.read())
                        fi.close()
                        importtype = getImportType(data, fpath[len(args.export_directory):], None)
                        creation_data = importtype.get_data()
                        creation_data['container'] = folder
                        creation_data['id'] = part
                        folder = api.content.create(**creation_data)
                        importtype.post_creation(folder)
                        if data['state']:
                            try:
                                api.content.transition(folder, to_state=data['state'])
                            except:
                                # maybe workflows do not match up
                                pass
                        folder.reindexObject()
                    else:
                        folder = api.content.create(
                            type='Folder',
                            id=part,
                            title=part.capitalize(),
                            container=folder)
                        bdata = ILayoutAware(folder)
                        bdata.contentLayout = '++contentlayout++castle/folder-query.html'
    return folder


_importable_fields = (
    'title',
    'description',
)


_read_phase = {}


def readObject(filepath):
    # disable, we don't use
    pass
    # fi = open(filepath)
    # data = mjson.loads(fi.read())
    # fi.close()


def fixHtmlImages(obj):
    try:
        html = obj.text.raw
    except:
        return
    if not html:
        return
    changes = False
    try:
        dom = fromstring(html)
    except:
        return
    for el in dom.cssselect('img'):
        src = el.attrib.get('src', '')
        if 'resolveuid' not in src:
            continue
        if '@@images' in src:
            continue
        parts = src.split('/')
        uid = parts[1]
        scale = '/'.join(parts[2:])
        if scale:
            scale = scale.replace('image_', '')
        src = 'resolveuid/%s/@@images/image' % uid
        if scale:
            src += '/' + scale
        attribs = {
            'src': src,
            'data-linktype': 'image',
            'data-val': uid
        }
        if scale:
            attribs['data-scale'] = scale
        el.attrib.update(attribs)
        changes = True
    if changes:
        obj.text = RichTextValue(
            tostring(dom), mimeType=obj.text.mimeType, outputMimeType=obj.text.outputMimeType)


def importObject(filepath, count):
    fi = open(filepath)
    data = mjson.loads(fi.read())
    fi.close()
    if filepath.endswith('__folder__'):
        filepath = '/'.join(filepath.split('/')[:-1])

    if data['portal_type'] in ('Topic', 'Collection', 'PressRoom'):
        return

    original_path = filepath[len(args.export_directory):]
    importtype = getImportType(data, original_path, _read_phase)
    path = importtype.get_path()
    folder = recursive_create_path('/'.join(path.split('/')[:-1]))
    _id = path.split('/')[-1]

    create = True
    if _id in folder.objectIds():
        if args.overwrite:
            if data['portal_type'] == 'Folder':
                cnt = folder[_id]
                if len(folder.objectIds()) == 1 or len(cnt.objectIds()) == 0:
                    api.content.delete(folder[_id])
            else:
                api.content.delete(folder[_id])
        else:
            create = False

    print('import path: %s' % path)
    creation_data = importtype.get_data()
    creation_data['container'] = folder

    aspect = ISelectableConstrainTypes(folder, None)
    if aspect:
        if (aspect.getConstrainTypesMode() != 1 or
                [creation_data['type']] != aspect.getImmediatelyAddableTypes()):
            aspect.setConstrainTypesMode(1)
            aspect.setImmediatelyAddableTypes([creation_data['type']])

    if create:
        obj = api.content.create(**creation_data)
    else:
        obj = folder[_id]
        for key, value in creation_data.items():
            if key not in ('id', 'type'):
                setattr(obj, key, value)

    if path != original_path:
        storage = getUtility(IRedirectionStorage)
        rpath = os.path.join('/'.join(site.getPhysicalPath()),
                             original_path.strip('/'))
        storage.add(rpath, "/".join(obj.getPhysicalPath()))

    importtype.post_creation(obj)
    if data['state']:
        try:
            api.content.transition(obj, to_state=data['state'])
        except:
            # maybe workflows do not match up
            pass

    fixHtmlImages(obj)
    obj.reindexObject()

    if count % 50 == 0:
        print('%i processed, committing' % count)
        transaction.commit()
        app._p_jar.invalidateCache()  # noqa
        transaction.begin()
        app._p_jar.sync()  # noqa


def importPages(path, count=0):
    for filename in os.listdir(path):
        if filename in ('.DS_Store', '__folder__'):
            continue
        count += 1
        filepath = os.path.join(path, filename)
        if os.path.isdir(filepath):
            count = importPages(filepath, count)
        else:
            try:
                importObject(filepath, count)
            except:
                logger.error('Error importing object', exc_info=True)
    return count


def importFolders(path, count=0):
    for filename in sorted(os.listdir(path)):
        count += 1
        filepath = os.path.join(path, filename)

        if filename == '__folder__':
            try:
                importObject(filepath, count)
            except:
                logger.error('Error importing object', exc_info=True)

        if os.path.isdir(filepath):
            count = importFolders(filepath, count)
    return count


def readPass(path):
    for filename in sorted(os.listdir(path)):
        if filename in ('.DS_Store', '__folder__'):
            continue
        filepath = os.path.join(path, filename)
        if os.path.isdir(filepath):
            readPass(filepath)
        else:
            readObject(filepath)


print('------------------------------')
print('Start importing')
print('------------------------------')
if args.overwrite:
    print('------------------------------')
    print('Importing with overwrite enabled')
    print('------------------------------')

print('doing read pass...')
# readPass(args.export_directory)
print('creating objects now...')
# importFolders(args.export_directory)
importPages(args.export_directory)
transaction.commit()
