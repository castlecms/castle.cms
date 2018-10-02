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
        "FormSelectionField"]))
args, _ = parser.parse_known_args()

ignore_uuids = args.ignore_uuids
stop_if_exception = args.stop_if_exception
pdb_if_exception = args.pdb_if_exception
skip_existing = args.skip_existing
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
    return '/'.join(obj.getPhysicalPath())[len('/'.join(site.getPhysicalPath())) + 1:]  # noqa


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
                        importtype = get_import_type(
                            data, fpath[len(args.export_directory):], None)
                        creation_data = importtype.get_data()
                        creation_data['container'] = folder
                        creation_data['id'] = part
                        created = False
                        if skip_existing and part in folder.objectIds():
                            print("    skipping existing %s" % part)
                        elif skip_types and creation_data['type'] in skip_types:  # noqa
                            print("    skipping %s (content type %s)" % (
                                part, creation_data['type']))
                        else:
                            try:
                                folder = api.content.create(**creation_data)
                                created = True
                            except api.exc.InvalidParameterError:
                                logger.error(
                                    'Error creating content {}'.format(fpath),
                                    exc_info=True)
                                if stop_if_exception:
                                    if pdb_if_exception:
                                        import pdb;pdb.set_trace()  # noqa
                                    raise
                                return
                        if created:
                            importtype.post_creation(folder)
                            if data['state']:
                                try:
                                    api.content.transition(
                                        folder, to_state=data['state'])
                                except Exception:
                                    logger.error(
                                        "maybe workflows do not match up")
                                    if stop_if_exception:
                                        if pdb_if_exception:
                                            import pdb;pdb.set_trace()  # noqa
                                        raise
                            folder.reindexObject()
                    else:
                        if skip_existing and part in folder.objectIds():
                            print("    skipping existing %s" % part)
                        else:
                            print("    creating folder %s" % part)
                            folder = api.content.create(
                                type='Folder',
                                id=part,
                                title=part.capitalize(),
                                container=folder)
                            bdata = ILayoutAware(folder)
                            bdata.contentLayout = '++contentlayout++castle/folder-query.html'  # noqa
    return folder


_importable_fields = (
    'title',
    'description',
)


_read_phase = {}


def read_object(filepath):
    # disable, we don't use
    pass
    # fi = open(filepath)
    # data = mjson.loads(fi.read())
    # fi.close()


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


def import_object(filepath, count):
    fi = open(filepath)
    file_read = fi.read()
    fi.close()
    try:
        data = mjson.loads(file_read)
    except Exception:
        print("    unable to read JSON data; skipping")
        return
    if filepath.endswith('__folder__'):
        filepath = '/'.join(filepath.split('/')[:-1])

    if data['portal_type'] in ('Topic', 'Collection', 'PressRoom'):
        return

    original_path = filepath[len(args.export_directory):]
    importtype = get_import_type(data, original_path, _read_phase)
    path = importtype.get_path()
    folder = recursive_create_path('/'.join(path.split('/')[:-1]))
    if folder is None:
        print('Skipped {} because of creation error'.format(filepath))
    _id = path.split('/')[-1]

    create = True
    if _id in folder.objectIds():
        if args.overwrite:
            if data['portal_type'] == 'Folder':
                cnt = folder[_id]
                if len(folder.objectIds()) == 1 or len(cnt.objectIds()) == 0:
                    print("    deleting folder %s" % _id)
                    api.content.delete(folder[_id])
            else:
                print("    deleting folder %s" % _id)
                api.content.delete(folder[_id])
        else:
            create = False

    print('import path: %s' % path)
    creation_data = importtype.get_data()
    # if creation_data['type'] in ['collective.cover.content', 'FormFolder']:
    if creation_data['type'] in skip_types:
        print('    skipping omitted type %s' % creation_data['type'])
        return  # skip objects of these types

    creation_data['container'] = folder

    aspect = ISelectableConstrainTypes(folder, None)
    if aspect:
        if (aspect.getConstrainTypesMode() != 1 or
                [creation_data['type']] != aspect.getImmediatelyAddableTypes()):  # noqa
            aspect.setConstrainTypesMode(1)
            aspect.setImmediatelyAddableTypes([creation_data['type']])

    if create:
        if ignore_uuids and '_plone.uuid' in creation_data:
            del creation_data['_plone.uuid']

        obj = None
        if (skip_existing and
                (_id in folder.objectIds() or
                 (not ignore_uuids and api.content.get(
                     UID=creation_data['_plone.uuid']) is not None))):
            print("    skipping existing %s" % _id)
        else:
            try:
                obj = api.content.create(safe_id=True, **creation_data)
            except api.exc.InvalidParameterError:
                if stop_if_exception:
                    logger.error('Error creating content {}'.format(filepath),
                                 exc_info=True)
                    if pdb_if_exception:
                        import pdb;pdb.set_trace()  # noqa
                    raise
                return logger.error(
                    'Error creating content {}'.format(filepath),
                    exc_info=True)
        # TODO set review_history
        review_history = data['review_history']
        wtool = api.portal.get_tool(name='portal_workflow')
        chain = wtool.getChainFor(obj)
        if len(chain) != 1:
            return logger.warning(
                'There should be only one workflow for this object %s but there are %s' % (obj, len(chain)))  # noqa
        workflow_id = chain[0]
        for h in review_history:
            wtool.setStatusOf(workflow_id, obj, h)

        # TODO check default folder pages came over as folder with
        #      rich text tile
        # TODO any folder pages without default page should have content
        #      listing tile
        # TODO get lead image captions
    else:
        obj = folder[_id]
        for key, value in creation_data.items():
            if key not in ('id', 'type'):
                setattr(obj, key, value)

    if obj is not None and path != original_path:
        storage = getUtility(IRedirectionStorage)
        rpath = os.path.join('/'.join(site.getPhysicalPath()),
                             original_path.strip('/'))
        storage.add(rpath, "/".join(obj.getPhysicalPath()))

    if obj is not None:
        importtype.post_creation(obj)
        if not args.skip_transitioning and data['state']:
            try:
                print("    transitioning %s to %s" % (obj.id, data['state']))
                api.content.transition(obj, to_state=data['state'])
            except Exception:
                logger.error("maybe workflows do not match up")
                if stop_if_exception:
                    if pdb_if_exception:
                        import pdb;pdb.set_trace()  # noqa
                    raise

        fix_html_images(obj)
        obj.reindexObject()

    if count % 50 == 0:
        print('%i processed, committing' % count)
        transaction.commit()
        app._p_jar.invalidateCache()  # noqa
        transaction.begin()
        app._p_jar.sync()  # noqa


def import_pages(path, count=0):
    for filename in os.listdir(path):
        if filename in ('.DS_Store', '__folder__'):
            continue
        count += 1
        filepath = os.path.join(path, filename)
        if os.path.isdir(filepath):
            count = import_pages(filepath, count)
        else:
            try:
                import_object(filepath, count)
            except Exception:
                logger.error('Error importing object', exc_info=True)
                if stop_if_exception:
                    if pdb_if_exception:
                        import pdb;pdb.set_trace()  # noqa
                    raise
    return count


def import_folders(path, count=0):
    for filename in sorted(os.listdir(path)):
        count += 1
        filepath = os.path.join(path, filename)

        if filename == '__folder__':
            try:
                import_object(filepath, count)
            except Exception:
                logger.error('Error importing object', exc_info=True)
                if stop_if_exception:
                    if pdb_if_exception:
                        import pdb;pdb.set_trace()  # noqa
                    raise

        if os.path.isdir(filepath):
            count = import_folders(filepath, count)
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
    print('------------------------------')
    print('Start importing')
    print('------------------------------')
    if args.overwrite:
        print('------------------------------')
        print('Importing with overwrite enabled')
        print('------------------------------')

    print('doing read pass...')
    # read_pass(args.export_directory)
    print('creating objects now...')
    # import_folders(args.export_directory)
    import_pages(args.export_directory)
    transaction.commit()
