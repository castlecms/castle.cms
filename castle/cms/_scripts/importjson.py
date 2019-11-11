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


_importable_fields = (
    'title',
    'description',
)


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


class CastleImporter(object):
    imported_count = 0

    def do_import(self):
        self.import_folder(args.export_directory, container=site)

    def import_object(self, filepath, container=None):
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

        if container is None:
            logger.warn('Skipped {} because of creation error'.format(filepath))
            return
        _id = path.split('/')[-1]

        create = True
        if _id in container.objectIds():
            if args.overwrite:
                existing = container[_id]
                if IFolder.providedBy(existing):
                    if len(existing.objectIds()):
                        print("OVERWRITE: Deleting non-empty container {path}".format(path=path))
                else:
                    print("OVERWRITE: Deleting content item at {path}".format(path=path))
                api.content.delete(container[_id])
            else:
                create = False

        creation_data = importtype.get_data()
        pc_data = importtype.get_post_creation_data()
        creation_data['container'] = container

        aspect = ISelectableConstrainTypes(container, None)
        if aspect:
            if (aspect.getConstrainTypesMode() != 1 or
                    [creation_data['type']] != aspect.getImmediatelyAddableTypes()):
                aspect.setConstrainTypesMode(1)
                aspect.setImmediatelyAddableTypes([creation_data['type']])
        if create:
            if ignore_uuids and '_plone.uuid' in creation_data:
                del creation_data['_plone.uuid']

            obj = None
            if not args.overwrite and (_id in container.objectIds()):
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
                    self.imported_count += 1
                    if self.imported_count % 50 == 0:
                        print('%i processed, committing' % self.imported_count)
                        transaction.commit()
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
            obj = container[_id]
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
            importtype.post_creation(obj, post_creation_data=pc_data)
            if not args.skip_transitioning and data['state']:
                # transition item only if it needs it
                state = api.content.get_state(obj=obj)
                if state != data['state']:
                    try:
                        print('Transitioning %s to %s' % (obj.id, data['state']))
                        api.content.transition(obj, to_state=data['state'])
                    except Exception:
                        logger.error("Error transitioning %s to %s, maybe workflows"
                                     " don't match up" % (obj.id, data['state']))
                        # pass
                        if stop_if_exception:
                            if pdb_if_exception:
                                pdb.set_trace()
                            raise

            # set workflow / review history
            if 'review_history' in data:
                review_history = data['review_history']
                wtool = api.portal.get_tool(name='portal_workflow')
                # loop over all workflow chains (usually only 1)
                for workflow_id in wtool.getChainFor(obj):
                    obj.workflow_history[workflow_id] = review_history
            else:
                logger.warn('No review history on {obj}'.format(obj=obj))

            fix_html_images(obj)
            obj.reindexObject()
            try:
                modification_date = data['data']['modification_date']
                obj.setModificationDate(modification_date)
                obj.reindexObject(idxs=['modified'])
                logger.info('    set modification date to %s' % modification_date)
            except Exception:
                logger.info('Could not set modification date on {obj}'
                                                                .format(obj=obj))
            return obj

    def import_folder(self, path, container):
        this_folder = os.path.join(path, '__folder__')
        if path is not args.export_directory:
            folder = None
            id = path.split('/')[-1:][0]
            if container and id in container.objectIds():
                if args.overwrite:
                    api.content.delete(container[id])
                else:
                    folder = container[id]
            if not folder:
                if os.path.exists(this_folder):
                    folder = self.import_object(this_folder, container)
                else:
                    folder = self.create_plain_folder(id, container)
            container = folder
        folders = []
        objects = []
        for filename in os.listdir(path):
            if filename in ('.DS_Store', '__folder__'):
                continue
            filepath = os.path.join(path, filename)
            if os.path.isdir(filepath):
                folders.append(filepath)
            else:
                objects.append(filepath)
        for path in folders:
            self.import_folder(path, container)
        for path in objects:
            try:
                self.import_object(path, container)
            except Exception:
                logger.error('Error importing {path}'.format(path=filepath),
                                                                exc_info=True)
                if stop_if_exception:
                    if pdb_if_exception:
                        pdb.set_trace()
                    raise

#    app._p_jar.invalidateCache()  # noqa
#    app._p_jar.sync()  # noqa

    def create_plain_folder(self, id, container):
        logger.info("Creating plain Folder (no __folder__ file found), %s" % id)
        folder = api.content.create(
            type='Folder',
            id=id,
            title=id.capitalize(),
            container=container)
        bdata = ILayoutAware(folder)
        bdata.contentLayout = '++contentlayout++castle/folder-query.html'
        if not args.skip_transitioning:
            api.content.transition(folder, to_state='published')
        return folder


if __name__ == '__main__':

    print('------------------------------')
    print('Start importing')
    print('------------------------------')
    if args.overwrite:
        print('------------------------------')
        print('Importing with overwrite enabled')
        print('------------------------------')
    importer = CastleImporter()
    importer.do_import()
    print('Created {count} Content Items'.format(count=importer.imported_count))
    transaction.commit()
