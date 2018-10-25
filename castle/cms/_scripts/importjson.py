from AccessControl.SecurityManagement import newSecurityManager
from castle.cms._scripts import mjson
from castle.cms._scripts.importtypes import get_import_type
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
import pdb

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
parser.add_argument('--site-id', dest='site_id', default='Castle')
parser.add_argument(
    '--export-directory', dest='export_directory', default='export')
parser.add_argument('--import-paths', dest='import_paths', default=False)
parser.add_argument('--skip-paths', dest='skip_paths', default=False)

parser.add_argument('--overwrite', dest='overwrite', default=False)
parser.add_argument('--admin-user', dest='admin_user', default='admin')
parser.add_argument('--ignore-uuids', dest='ignore_uuids', default=False)
parser.add_argument(
    '--stop-if-exception', dest='stop_if_exception', default=False)
parser.add_argument(
    '--pdb-if-exception', dest='pdb_if_exception', default=False)
parser.add_argument('--skip-existing', dest='skip_existing', default=True)
parser.add_argument(
    '--skip-transitioning', dest='skip_transitioning', default=False)
parser.add_argument(
    '--skip-types', dest='skip_types', default=','.join([
        "collective.cover.content",
        "FormFolder",
        "FormMailerAdapter",
        "FormTextField",
        "FormStringField",
        "FormThanksPage",
        "FormSaveDataAdapter",
        "FormSaveData2ContentAdapter",
        "FormSelectionField",
        "Topic"]))
parser.add_argument('--only-types', dest='only_types', default=False)

# Put files/videos/etc in to the repository paths by default,
# Set true to retain exported path
parser.add_argument('--retain-paths', dest='retain_paths', default=False)

args, _ = parser.parse_known_args()

ignore_uuids = args.ignore_uuids
stop_if_exception = args.stop_if_exception
pdb_if_exception = args.pdb_if_exception
retain_paths = args.retain_paths

if args.import_paths:
    import_paths = args.import_paths.split(',')
else:
    import_paths = False
if args.skip_paths:
    skip_paths = args.skip_paths.split(',')
else:
    skip_paths = False


if args.only_types:
    only_types = args.only_types.split(',')
else:
    only_types = False
if args.skip_types:
    skip_types = args.skip_types.split(',')
else:
    skip_types = False

user = app.acl_users.getUser(args.admin_user)  # noqa
try:
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa
except Exception:
    logger.error('Unknown admin user; '
                 'specify an existing Zope admin user with --admin-user '
                 '(default is admin)')
    exit(-1)
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
    return '/'.join(obj.getPhysicalPath())[len(
        '/'.join(site.getPhysicalPath())) + 1:]


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
                        logger.warn('Existing object in traversal path is not folderish. Removing it.')
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
                    imported = False
                    if os.path.exists(fpath):
                        imported = import_object(fpath)
                    if not imported:
                        logger.info("Creating plain Folder (no __folder__ file found), %s" % part)
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


def read_object(filepath):
    # disable, we don't use
    pass


def fix_html_images(obj):
    try:
        html = obj.text.raw
    except Exception:
        return
    if not html:
        return
    changes = False
    try:
        dom = fromstring(html)
    except Exception:
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
            tostring(dom), mimeType=obj.text.mimeType,
            outputMimeType=obj.text.outputMimeType)


def import_object(filepath):
    fi = open(filepath)
    file_read = fi.read()
    fi.close()
    try:
        data = mjson.loads(file_read)
    except Exception:
        print("Skipping {}; Unable to read JSON data".format(filepath))
        return
    if filepath.endswith('__folder__'):
        filepath = '/'.join(filepath.split('/')[:-1])

    skipped = False
    if data['portal_type'] in skip_types:
        print('Skipping omitted type {type}'
                                        .format(type=data['portal_type']))
        skipped = True
    if only_types and data['portal_type'] not in only_types:
        print("Skipping {type} at {path}, not in only_types."
                            .format(type=data['portal_type'], path=filepath))
        skipped = True
    if import_paths:
        do_import = False
        for import_path in import_paths:
            if filepath.startswith('{}/{}'.format(args.export_directory, import_path)):
                do_import = True
            if import_path.startswith(filepath[len(args.export_directory):].lstrip('/') + '/'):
                # Don't skip folders on the way to import_paths
                do_import = True
        if not do_import:
            print("Skipping {path}, not in import_paths"
                                .format(path=filepath))
            skipped = True
    if skip_paths:
        for skip_path in skip_paths:
            if filepath.lower().startswith('{}/{}'.format(args.export_directory, skip_path)):
                print("Skipping {path}, in skip_paths"
                                .format(path=filepath))
                skipped = True
    if skipped:
        if os.path.isdir(filepath) and len(os.listdir(filepath)):
            logger.warn('{path} contains additional content that will be '
                        'skipped.'.format(path=filepath))
        return

    original_path = filepath[len(args.export_directory):]
    if retain_paths:
        importtype = get_import_type(data, original_path, 'retain_paths')
    else:
        importtype = get_import_type(data, original_path)
    path = importtype.get_path()

    folder = recursive_create_path('/'.join(path.split('/')[:-1]))
    if folder is None:
        logger.warn('Skipped {} because of creation error'.format(filepath))
        return
    _id = path.split('/')[-1]

    create = True
    if _id in folder.objectIds():
        if args.overwrite:
            existing = folder[_id]
            if IFolder.providedBy(existing):
                if len(existing.objectIds()):
                    print("OVERWRITE: Deleting non-empty folder {path}".format(path=path))
            else:
                print("OVERWRITE: Deleting content item at {path}".format(path=path))
            api.content.delete(folder[_id])
        else:
            create = False

    creation_data = importtype.get_data()
    creation_data['container'] = folder

    aspect = ISelectableConstrainTypes(folder, None)
    if aspect:
        if (aspect.getConstrainTypesMode() != 1 or
                [creation_data['type']] != aspect.getImmediatelyAddableTypes()):
            aspect.setConstrainTypesMode(1)
            aspect.setImmediatelyAddableTypes([creation_data['type']])

    if create:
        if ignore_uuids and '_plone.uuid' in creation_data:
            del creation_data['_plone.uuid']

        obj = None
        if not args.overwrite and (_id in folder.objectIds()):
            print('Skipping {path}, already exists. Use --overwrite to'
                                        ' create anyway.'.format(path=path))
            return
        elif (not ignore_uuids and api.content.get(UID=creation_data['_plone.uuid']) is not None):
            logger.warn('Skipping {path}, content with its UUID already exists.'
                                        'Use --ignore-uuids to create anyway.'
                                                            .format(path=path))
            return
        else:
            try:
                obj = api.content.create(safe_id=True, **creation_data)
                print('Created {path}'.format(path=path))
            except api.exc.InvalidParameterError:
                if stop_if_exception:
                    logger.error('Error creating content {}'.format(filepath), exc_info=True)
                    if pdb_if_exception:
                        pdb.set_trace()
                    raise
                logger.error('Error creating content {}'
                                            .format(filepath), exc_info=True)
                return


# TODO check default folder pages came over as folder with rich text tile
# TODO any folder pages without default page should have content listing tile
    else:
        obj = folder[_id]
        for key, value in creation_data.items():
            if key not in ('id', 'type'):
                setattr(obj, key, value)

    if obj is not None:
        if path != original_path:
            storage = getUtility(IRedirectionStorage)
            rpath = os.path.join('/'.join(site.getPhysicalPath()),
                                 original_path.strip('/'))
            storage.add(rpath, "/".join(obj.getPhysicalPath()))

        obj.contentLayout = importtype.layout
        importtype.post_creation(obj)
        if not args.skip_transitioning and data['state']:
            try:
                print('Transitioning %s to %s' % (obj.id, data['state']))
                api.content.transition(obj, to_state=data['state'])
            except Exception:
                logger.error("Error transitioning %s to %s, maybe workflows"
                                "don't match up" % (obj.id, data['state']))
                # pass
                if stop_if_exception:
                    if pdb_if_exception:
                        pdb.set_trace()
                    raise

        # set workflow / review history
        if 'review_history' in data:
            review_history = data['review_history']
            wtool = api.portal.get_tool(name='portal_workflow')
            chain = wtool.getChainFor(obj)
            if len(chain):
                workflow_id = chain[0]
                for h in review_history:
                    wtool.setStatusOf(workflow_id, obj, h)
                if len(chain) != 1:
                    return logger.warn('There should be 1 workflow for %s but'
                                        'there are %i' % (path, len(chain)))
        else:
            return logger.warn('No review history on {obj}'.format(obj=obj))

        fix_html_images(obj)
        obj.reindexObject()
        return True


def import_content(path, count=0):
    this_folder = os.path.join(path, '__folder__')
    if os.path.exists(this_folder):
        imported = import_object(this_folder)
        if imported:
            count += 1
        else:
            # folder object exists in export,but errored or was skipped
            return count
    for filename in os.listdir(path):
        if filename in ('.DS_Store', '__folder__'):
            continue
        filepath = os.path.join(path, filename)
        if os.path.isdir(filepath):
            count = import_content(filepath, count)
        else:
            try:
                imported = import_object(filepath)
                if imported:
                    count += 1
            except Exception:
                logger.error('Error importing {path}'.format(path=filepath),
                                                                exc_info=True)
                if stop_if_exception:
                    if pdb_if_exception:
                        pdb.set_trace()
                    raise
        if count and count % 50 == 0:
            print('%i processed, committing' % count)
            transaction.commit()
            app._p_jar.invalidateCache()  # noqa
            transaction.begin()
            app._p_jar.sync()  # noqa
    if path == args.export_directory:
        transaction.commit()
        app._p_jar.invalidateCache()  # noqa
    return count


def read_pass(path):
    for filename in sorted(os.listdir(path)):
        if filename in ('.DS_Store', '__folder__'):
            continue
        filepath = os.path.join(path, filename)
        if os.path.isdir(filepath):
            read_pass(filepath)
        else:
            read_object(filepath)


if __name__ == '__main__':
    # logger.info('Doing read pass...')
    # read_pass(args.export_directory)

    print('------------------------------')
    print('Start importing')
    print('------------------------------')
    if args.overwrite:
        print('------------------------------')
        print('Importing with overwrite enabled')
        print('------------------------------')
    count = import_content(args.export_directory)
    print('Created {count} Content Items'.format(count=count))
    transaction.commit()
