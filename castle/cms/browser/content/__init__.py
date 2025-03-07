import json
import logging
import math
import os
import plone.api as api
import re
import shutil
import tempfile
import time

from mimetypes import guess_type
from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms import commands
from castle.cms import utils
from castle.cms.archival import SubrequestUrlOpener
from castle.cms.browser.utils import Utils
from castle.cms.commands import exiftool
from castle.cms.commands import qpdf
from castle.cms.files import duplicates
from castle.cms.interfaces import ITrashed
from castle.cms.utils import get_template_repository_info
from castle.cms.utils import get_upload_fields
from castle.cms.utils import publish_content
from lxml.html import fromstring
from OFS.interfaces import IFolder
from OFS.ObjectManager import checkValidId
from persistent.dict import PersistentDict
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.vocabularies import AvailableSiteLayouts
from plone.app.content.browser import i18n
from plone.app.drafts.utils import getCurrentDraft
from plone.app.layout.navigation.defaultpage import getDefaultPage
from plone.app.linkintegrity.utils import getOutgoingLinks
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.interfaces import IDexterityContainer
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from plone.registry import Record
from plone.registry import field as registry_field
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone import utils as ploneutils
from Products.CMFPlone.browser.syndication.adapters import SearchFeed
from Products.CMFPlone.interfaces import ISelectableConstrainTypes
from Products.CMFPlone.interfaces.syndication import IFeedItem
from Products.DCWorkflow.Expression import StateChangeInfo
from Products.DCWorkflow.Expression import createExprContext
from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION
from Products.Five import BrowserView
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component.hooks import getSite
from zope.container.interfaces import INameChooser
from zope.interface.declarations import noLongerProvides


try:
    # Python 2.6-2.7
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser


html_parser = HTMLParser()


logger = logging.getLogger('castle.cms')


def dump_object_data(obj, duplicate=False):
    try:
        state = api.content.get_state(obj=obj)
    except WorkflowException:
        state = 'published'
    base_url = obj.absolute_url()
    registry = getUtility(IRegistry)
    if obj.portal_type in registry.get('plone.types_use_view_action_in_listings', []):
        url = base_url + '/view'
    else:
        url = base_url
    return json.dumps({
        'success': True,
        'base_url': base_url,
        'url': url,
        'edit_url': base_url + '/@@edit',
        'portal_type': obj.portal_type,
        'uid': IUUID(obj),
        'workflow_state': state,
        'title': obj.Title(),
        'valid': True,
        'duplicate': duplicate
    })


class Workflow(BrowserView):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        if self.request.form.get('action') == 'transition':
            return self.transition()

    def transition(self):
        form = self.request.form
        transition_id = form.get('transition_id')
        comment = form.get('comment', '')
        api.content.transition(obj=self.context, transition=transition_id, comment=comment)
        return json.dumps({
            'success': True
        })


class TmpUploadFile(object):
    def __init__(self, load=False, filename=None, chunk_size=None, total_size=None, prefix=None):
        self.base_tmp_dir = os.getenv("CASTLECMS_TMP_FILE_DIR", tempfile.gettempdir())

        if load:
            self.metadata_path = os.path.join(self.base_tmp_dir, prefix, "metadata.json")
            self.load()
            return

        _id = utils.get_random_string(50)
        self.prefix = prefix + _id
        self.tmp_dir = os.path.join(self.base_tmp_dir, self.prefix)
        self.metadata_path = os.path.join(self.base_tmp_dir, self.prefix, "metadata.json")
        self.info = dict(
            id=_id,
            tmp_dir=self.tmp_dir,
            tmp_file=os.path.join(self.tmp_dir, filename),
            last_chunk=1,
            chunk_size=chunk_size,
            total_size=total_size,
            name=filename,
        )
        os.makedirs(self.tmp_dir)

    def load(self):
        with open(self.metadata_path, 'r') as fin:
            self.info = json.load(fin)

    def save(self):
        with open(self.metadata_path, 'w') as fout:
            json.dump(self.info, fout, indent=2)

    def write_chunk(self, chunk, formdata):
        mode = 'wb'
        if chunk > 1:
            mode = 'ab+'
            # if we're not on the first chunk, and there's no temp file, then
            # there's an issue
            if not os.path.exists(self.info['tmp_file']):
                raise Exception('No tmp upload file found')
        with open(self.info['tmp_file'], mode) as fin:
            while True:
                data = formdata.read(2 << 16)
                if not data:
                    break
                fin.write(data)

    def cleanup(self):
        # tmp_ files need to stick around and be managed later
        if not self.info.get('field_name', '').startswith('tmp_'):
            shutil.rmtree(self.info["tmp_dir"])

    def check(self, chunk, chunk_size, total_size):
        # check things are matching up
        if self.info['last_chunk'] != chunk - 1:
            raise Exception('Invalid chunk sequence')
        if self.info['total_size'] != total_size:
            raise Exception('Invalid total size')
        if self.info['chunk_size'] != chunk_size:
            raise Exception('Inconsistent chunk size')


class Creator(BrowserView):
    """
    Advanced content creation view.
    """
    status = ''

    def __call__(self):
        self.sm = getSecurityManager()
        self.request.response.setHeader('Content-type', 'application/json')
        if api.user.is_anonymous():
            self.request.response.setStatus(403)
            return json.dumps({
                'reason': 'No access'
            })
        self.catalog = api.portal.get_tool('portal_catalog')
        action = self.request.form.get('action')
        if action == 'check':
            return self.check()
        elif action == 'create':
            return self.create()
        elif action == 'create-from-template':
            return self.create_object_from_template()
        elif action == 'remove':
            return self.remove_file_content()
        elif action == 'chunk-upload':
            return self.chunk_upload()

    def chunk_upload(self):
        chunk = int(self.request.form['chunk'])
        chunk_size = int(self.request.form['chunkSize'])
        total_size = int(self.request.form['totalSize'])
        total_chunks = int(math.ceil(float(total_size) / float(chunk_size)))
        _id = self.request.form.get('id')
        existing_id = self.request.form.get('content', None)
        field_name = self.request.form.get('field', None)

        if chunk > total_chunks:
            raise Exception("More chunks than what should be possible")

        cache_key_prefix = '%s-uploads-' % '-'.join(self.context.getPhysicalPath()[1:])
        if chunk == 1:
            tmp_file = TmpUploadFile(
                filename=self.request.form['name'],
                chunk_size=chunk_size,
                total_size=total_size,
                prefix=cache_key_prefix)

        else:
            tmp_file = TmpUploadFile(load=True, prefix=cache_key_prefix + _id)
            tmp_file.check(chunk, chunk_size, total_size)
            tmp_file.info['last_chunk'] = chunk

        tmp_file.write_chunk(chunk, self.request.form['file'])

        if chunk == total_chunks:
            # finish upload
            dup = False
            if not existing_id:
                try:
                    obj = self.create_file_content(tmp_file.info)
                except duplicates.DuplicateException as ex:
                    obj = ex.obj
                    dup = True
            else:
                try:
                    tmp_file.info['existing_id'] = existing_id
                    tmp_file.info['field_name'] = field_name
                    obj, success, msg = self.update_file_content(tmp_file.info)
                    if not success:
                        self.update_file_content(tmp_file.info)
                        self._clean_tmp(tmp_file.info)
                        return json.dumps({
                            'success': False,
                            'id': tmp_file.info["id"],
                            'reason': msg
                        })
                except Exception:
                    logger.warning(
                        'Failed to update content.', exc_info=True)
                    self._clean_tmp(tmp_file.info)
                    return json.dumps({
                        'success': False,
                        'id': tmp_file.info["id"]
                    })
            tmp_file.cleanup()
            return dump_object_data(obj, dup)
        else:
            tmp_file.save()

        return json.dumps({
            'success': True,
            'id': tmp_file.info["id"]
        })

    def _clean_tmp(self, info):
        tmp_dir = '/'.join(info['tmp_file'].split('/')[:-1])
        shutil.rmtree(tmp_dir)

    def detect_duplicate(self, info):
        dup_detector = duplicates.DuplicateDetector()
        md5_hash = commands.md5(info['tmp_file'])
        obj = dup_detector.get_object(md5_hash)
        if obj is not None:
            # found, use existing file...
            raise duplicates.DuplicateException(obj)
        return dup_detector, md5_hash

    def handle_auto_folder_creation(self, folder, type_):
        # we only auto publish built-in repositories, otherwise, leave it be
        try:
            if api.content.get_state(obj=folder) not in ('published', 'publish_internally'):
                publish_content(folder)
        except WorkflowException:
            pass

        aspect = ISelectableConstrainTypes(folder, None)
        if aspect:
            should_set_constrain_types = (
                aspect.getConstrainTypesMode() != 1 or
                [type_] != aspect.getImmediatelyAddableTypes()
            )
            if should_set_constrain_types:
                aspect.setConstrainTypesMode(1)
                try:
                    aspect.setImmediatelyAddableTypes([type_])
                except Exception:
                    pass

        if not getattr(folder, 'exclude_from_nav', False):
            # if auto generated path, exclude from nav
            folder.exclude_from_nav = True
            folder.reindexObject()

    def get_type_and_location(self, info):
        filename = info['name']
        ext = os.path.splitext(filename)[-1]
        registry = getUtility(IRegistry)
        type_ = 'File'
        location = registry.get('file_repo_location', '/file-repository')
        if ext.lower() in ['.jpg', '.jpeg', '.gif', '.png']:
            type_ = 'Image'
            location = registry.get(
                'image_repo_location', '/image-repository')
        elif ext.lower() in ['.webm', '.ogv', '.avi', '.wmv', '.m4v',
                             '.mpg', '.mpeg', '.flv', '.mp4', '.mov']:
            type_ = 'Video'
            location = registry.get(
                'video_repo_location', '/video-repository')
        elif ext.lower() in ['.mp3']:
            type_ = 'Audio'
            location = registry.get(
                'audio_repo_location', '/audio-repository')
        return type_, location

    def update_file_content(self, info):
        type_, location = self.get_type_and_location(info)
        obj = uuidToObject(info['existing_id'])
        success = False
        msg = None
        if obj:
            if self.sm.checkPermission(ModifyPortalContent, obj):
                try:
                    if info['field_name'].startswith('tmp_'):
                        self.add_tmp_upload(obj, info)
                    else:
                        fi = open(info['tmp_file'], 'r')
                        filename = ploneutils.safe_unicode(info['name'])
                        if 'Image' in type_:
                            blob = NamedBlobImage(data=fi, filename=filename)
                        else:
                            blob = NamedBlobFile(data=fi, filename=filename)
                        setattr(obj, info['field_name'], blob)
                    success = True
                except Exception:
                    # could not update content
                    logger.warning('Error updating content', exc_info=True)
                    msg = 'Unknown error'
            else:
                msg = 'Invalid permissions'
        else:
            success = False
            msg = 'Object not found'
        return obj, success, msg

    def add_tmp_upload(self, obj, info):
        annotations = IAnnotations(obj)
        if '_tmp_files' not in annotations:
            annotations['_tmp_files'] = PersistentDict()
        tmp_files = annotations['_tmp_files']

        # cleanup old ones
        for tmp_id, item in [(k, v) for k, v in tmp_files.items()]:
            if (time.time() - item['uploaded']) > (1 * 60 * 60):
                del tmp_files[tmp_id]
        info['uploaded'] = time.time()
        tmp_files[info['field_name']] = info

    def remove_file_content(self):
        id = self.request.form.get('content', None)
        field = self.request.form.get('field', None)
        if id and field:
            obj = uuidToObject(id)
            if obj:
                if self.sm.checkPermission(ModifyPortalContent, obj):
                    setattr(obj, field, None)

    def create_file_content(self, info):
        type_, location = self.get_type_and_location(info)
        original_location = location

        if self.request.form.get('location'):
            location = self.request.form['location']

        original_location == location
        folder = utils.recursive_create_path(self.context, location)

        md5_hash = dup_detector = None

        if original_location == location:
            # first off, check first that it wasn't already uploaded...
            # we are only checking images for now...
            if type_ == 'Image' and commands.md5:
                dup_detector, md5_hash = self.detect_duplicate(info)
            self.handle_auto_folder_creation(folder, type_)

        obj = self.create_object(folder, type_, info)
        if type_ == 'Image' and md5_hash and dup_detector:
            dup_detector.register(obj, md5_hash)
        return obj

    def create_object(self, folder, type_, info):
        filename = info['name']
        name = filename.decode("utf8")
        chooser = INameChooser(folder)
        chooser_name = name.lower().replace('aq_', '')
        newid = chooser.chooseName(chooser_name, folder.aq_parent)
        # strip metadata from file
        if (type_ in ('Image', 'File', 'Video') and
                exiftool is not None and 'tmp_file' in info):
            is_pdf = ('application/pdf' in guess_type(info['tmp_file']))
            if is_pdf and qpdf is not None:
                try:
                    # Will recursively remove the tags of the file using exiftool, linearize it.
                    # And do it again.
                    exiftool(info['tmp_file'])
                    qpdf(info['tmp_file'])
                    exiftool(info['tmp_file'])
                    qpdf(info['tmp_file'])
                except Exception:
                    logger.warn('Could not strip additional metadata with qpdf %s' % info['tmp_file'])
            else:
                try:
                    exiftool(info['tmp_file'])
                except Exception:
                    logger.warn('Could not strip metadata from file: %s' % info['tmp_file'])

        fi = open(info['tmp_file'], 'r')
        try:
            # Try to determine which kind of NamedBlob we need
            # This will suffice for standard p.a.contenttypes File/Image
            # and any other custom type that would have 'File' or 'Image' in
            # its type name
            filename = ploneutils.safe_unicode(filename)
            create_opts = dict(
                type=type_,
                id=newid,
                container=folder)
            if 'Image' in type_:
                image = NamedBlobImage(data=fi, filename=filename)
                try:
                    image.focal_point = [
                        float(self.request.form.get('focalX')),
                        float(self.request.form.get('focalY'))
                    ]
                except Exception:
                    pass
                create_opts['image'] = image
            else:
                create_opts['file'] = NamedBlobFile(data=fi, filename=filename)

            for field in get_upload_fields():
                if not field.get('name'):
                    continue
                name = field['name']
                if not self.request.form.get(name):
                    continue
                if name in ('tags', 'subject'):
                    # tags needs to be converted
                    create_opts['subject'] = self.request.form.get(name).split(';')
                else:
                    create_opts[name] = self.request.form.get(name, '')
            return api.content.create(**create_opts)
        finally:
            fi.close()

    def get_type_id(self):
        form = self.request.form
        type_id = form.get('selectedType[unformattedPortalType]', None)
        if type_id is None:
            type_id = form.get('selectedType[typeId]', None)
        if type_id is None:
            type_id = form.get('selectedType[id]', '') or ''
        return type_id.replace('%20', ' ')

    def create(self):
        if self._check():
            path = self.request.form.get('basePath', '/')
            folder = utils.recursive_create_path(self.context, path)
            obj = api.content.create(
                type=self.get_type_id(),
                id=self.request.form['id'],
                title=self.request.form['title'],
                container=folder)
            transition_to = self.request.form.get('transitionTo')
            if transition_to:
                try:
                    api.content.transition(obj=obj, transition=transition_to)
                except Exception:
                    pass
            return dump_object_data(obj)
        else:
            return json.dumps({
                'valid': False,
                'status': 'Unknown error creating content'
            })

    def get_folder(self):
        folder = None
        path = self.request.form.get('basePath', '/')
        if path == '/':
            folder = self.context
        else:
            path = path.lstrip('/')
            folder = self.context.restrictedTraverse(path, None)
            if folder is None:
                # check parents to see if we can auto create structure
                path = '/'.join(path.split('/')[:-1])
                while path:
                    folder = self.context.restrictedTraverse(path, None)
                    if folder:
                        if not IFolder.providedBy(folder):
                            self.status = 'Not a valid path.'
                            return None
                        break
                    path = '/'.join(path.split('/')[:-1])
                if not folder:
                    self.status = """Will automatically create folder(s) to place
content in this location."""
                    folder = self.context
            elif not IFolder.providedBy(folder):
                self.status = 'Not a valid path.'
                return None

        return folder

    def can_add(self, folder, type_id):
        constraints = ISelectableConstrainTypes(folder, None)
        addable = None
        if constraints is not None:
            addable = constraints.getLocallyAllowedTypes()

        if addable is None:
            addable = [t.getId() for t in folder.allowedContentTypes()]

        if type_id not in addable:
            return False
        return True

    def valid_id(self, container, id):
        if id in ('path', 'id', 'start'):
            return False
        try:
            checkValidId(container, id, False)
            obj = getattr(self, id, None)
            if obj is not None:
                if id not in container.objectIds():
                    return False
        except Exception:
            return False
        return True

    def _check(self, folder=None):
        valid = True
        if folder is None:
            folder = self.get_folder()
        if folder is not None:
            portal_types = getToolByName(self.context, 'portal_types')
            type_id = self.get_type_id()

            add_permission = portal_types[type_id].add_permission
            add_permission_title = utils.get_permission_title(add_permission)

            if valid and not self.can_add(folder, type_id):
                valid = False
                self.status = 'You are not allowed to add this content type here'
            elif valid and not self.sm.checkPermission(add_permission_title, folder):
                valid = False
                self.status = 'You do not have permission to add content here.'
            elif valid and self.request.form['id'] in folder.objectIds():
                valid = False
                ob = folder[self.request.form['id']]
                if ITrashed.providedBy(ob):
                    self.status = (
                        'Content in recycling bin with same id exists. '
                        'Delete, rename or restore recycled content to use this.'
                    )
                else:
                    self.status = 'Content with same ID already exists'
            elif not self.valid_id(folder, self.request.form['id']):
                valid = False
                self.status = '"%s" is not valid to be used in a path' % self.request.form['id']
        else:
            valid = False
            if not self.status:
                self.status = 'Could not validate folder'

        for idx, part in enumerate(self.request.form.get('basePath', '/').split('/')):
            if not part:
                continue
            if part in self.context:
                continue
            if not self.valid_id(self.context, part):
                valid = False
                self.status = '"%s" is not valid to be used in a path' % part
                break
        return valid, folder

    def get_workflow_info(self, folder):
        type_id = self.get_type_id()
        wf_tool = api.portal.get_tool('portal_workflow')
        cbt = wf_tool._chains_by_type
        chain = cbt.get(type_id, None)
        if chain is None:
            chain = wf_tool.getDefaultChain()

        if len(chain) == 0:
            state_info = None
        else:
            wf = wf_tool[chain[0]]
            initial_state = wf.states[wf.initial_state]
            state_info = {
                'initial': {
                    'id': initial_state.id,
                    'title': initial_state.title
                }
            }
            possible_states = {}

            for transition_id in initial_state.transitions:
                transition = wf.transitions.get(transition_id, None)
                if (transition is None or
                        transition.trigger_type != TRIGGER_USER_ACTION or
                        not transition.actbox_name):
                    continue
                try:
                    new_state = wf.states[transition.new_state_id]
                except Exception:
                    continue
                if transition.new_state_id in possible_states:
                    # we can already get here... don't worry about it, ignore
                    continue
                checker = WorkflowPermissionChecker(initial_state, folder)
                if checker.has_permission(transition):
                    possible_states[transition.new_state_id] = {
                        'title': new_state.title,
                        'transition': transition_id
                    }
            state_info['possible_states'] = possible_states

        return state_info

    def check(self):
        valid, folder = self._check()

        if valid:
            info = self.get_workflow_info(folder)
        else:
            info = None

        return json.dumps({
            'valid': valid,
            'status': self.status,
            'stateInfo': info
        })

    def create_object_from_template(self):
        if self._check():
            template_title = self.request.form.get('selectedType[title]')
            new_id = self.request.form.get('id')
            new_title = self.request.form.get('title')
            path = self.request.form.get('basePath', '/')
            folder = utils.recursive_create_path(self.context, path)
            for template in get_template_repository_info()['templates']:
                if template.title == template_title:
                    obj = api.content.copy(
                        source=template,
                        id=new_id,
                        target=folder
                    )
                    obj.title = new_title

            transition_to = self.request.form.get('transitionTo')
            if transition_to:
                try:
                    api.content.transition(obj=obj, transition=transition_to)
                except Exception:
                    pass
            return dump_object_data(obj)
        else:
            return json.dumps({
                'valid': False,
                'status': 'Unknown error creating content'
            })


class WorkflowPermissionChecker(object):

    def __init__(self, initial_state, folder):
        self.folder = folder
        self.initial_state = initial_state
        self.sm = getSecurityManager()
        self.user = self.sm.getUser()
        self.folder_roles = self.user.getRolesInContext(folder)
        self._u_groups = None

    @property
    def u_groups(self):
        if self._u_groups is not None:
            return self._u_groups

        b = aq_base(self.user)
        if hasattr(b, 'getGroupsInContext'):
            u_groups = self.user.getGroupsInContext(self.folder)
        elif hasattr(b, 'getGroups'):
            u_groups = self.user.getGroups()
        else:
            u_groups = ()
        self._u_groups = u_groups
        return u_groups

    def has_permission(self, transition):
        guard = transition.guard
        if guard is None:
            return True

        for permission in guard.permissions or []:
            # need to manually check permissions here because
            # we don't have an object to check against
            check_parent = True
            if permission in self.initial_state.permissions:
                # check if acquire set for initial_state.
                # if acquire, you can check against parent
                pinfo = self.initial_state.getPermissionInfo(permission)
                if pinfo.get('acquired'):
                    check_parent = True
                else:
                    check_parent = False
                    if len(set(self.folder_roles) & set(pinfo['roles'])) > 0:
                        break
            if check_parent:
                if self.sm.checkPermission(permission, self.folder):
                    break
        else:
            # no perms valid...
            return False

        if guard.roles:
            for role in guard.roles:
                if role in self.folder_roles:
                    break
            else:
                return False

        if guard.groups:
            for group in guard.groups:
                if group in self.u_groups:
                    break
            else:
                return False

        if guard.expr is not None:
            econtext = createExprContext(
                StateChangeInfo(self.folder, aq_parent(aq_parent(self.initial_state))))
            res = guard.expr(econtext)
            if not res:
                return False

        return True


class BackendUrlUtils(object):
    # start of string
    # optional http:// or https:// is catured as 'protocol'
    # optional leading slashes are captured as 'leading_slashes'
    # everything else is captured as 'url'
    URL_PATTERN = r'^(?P<protocol>https?:\/\/)?(?P<leading_slashes>\/+)?(?P<url>.*)$'
    UNSET = object()
    _public_url = UNSET
    _backend_urls = UNSET
    _invalid_backend_urls = UNSET

    @property
    def backend_urls(self):
        if getattr(self, '_backend_urls', self.UNSET) is self.UNSET:
            formatted_backend_urls = []
            backend_urls = api.portal.get_registry_record('plone.backend_url', default=[]) or []
            for backend_url in backend_urls:
                formatted_url = self.get_formatted_url(backend_url)
                if formatted_url and isinstance(formatted_url, basestring):
                    formatted_backend_urls.append(formatted_url)
            self._backend_urls = formatted_backend_urls
        return self._backend_urls

    @property
    def public_url(self):
        if getattr(self, '_public_url', self.UNSET) is self.UNSET:
            public_url = api.portal.get_registry_record('plone.public_url', default=None) or None
            if public_url and isinstance(public_url, basestring):
                self._public_url = public_url
            else:
                self._public_url = None
        return self._public_url

    @property
    def invalid_backend_urls(self):
        # if a site has the same backend and public url, do not consider it invalid
        if getattr(self, '_invalid_backend_urls', self.UNSET) is self.UNSET:
            public_url = self.public_url
            backend_urls = self.backend_urls
            if public_url is None:
                self._invalid_backend_urls = backend_urls
            else:
                self._invalid_backend_urls = [
                    backend_url
                    for backend_url in backend_urls
                    if backend_url != public_url
                ]
        return self._invalid_backend_urls

    def get_formatted_url(self, url):
        try:
            # probably the only way to not get a match here is a non-string
            match = re.match(self.URL_PATTERN, url)
            return match.groupdict()['url']
        except Exception:
            return None

    def get_invalid_backend_urls_found(self, content):
        return [
            invalid_backend_url
            for invalid_backend_url in self.invalid_backend_urls
            if invalid_backend_url in content
        ]


class QualityCheckContent(BrowserView):
    QUALITY_CHECK_URL = '/@@quality-check'

    @property
    def formatted_url(self):
        try:
            end_index = None
            if self.request.URL.endswith(self.QUALITY_CHECK_URL):
                end_index = -1 * len(self.QUALITY_CHECK_URL)
            return self.request.URL[:end_index]
        except Exception:
            return None

    @property
    def subrequest_results(self):
        opener = SubrequestUrlOpener(
            site=api.portal.get(),
            check_blacklist=False,
        )
        return opener(self.formatted_url, require_public_url=False)

    @property
    def contains_backend_urls(self):
        subrequest_results = self.subrequest_results
        subrequest_html = subrequest_results['data']
        backend_utils = BackendUrlUtils()
        backend_urls_found = backend_utils.get_invalid_backend_urls_found(subrequest_html)
        if len(backend_urls_found) > 0:
            logger.warn('There were backend urls found in the html')
            logger.info('Backend urls found: {}'.format(repr(backend_urls_found)))
            logger.info('Data searched for: ' + self.formatted_url)
            return True
        return False

    @property
    def are_links_valid(self):
        for link in getOutgoingLinks(self.context):
            state = api.content.get_state(obj=link.to_object, default='published')
            if state != 'published':
                return False
        return True

    @property
    def html(self):
        try:
            feed = SearchFeed(api.portal.get())
            adapter = queryMultiAdapter((self.context, feed), IFeedItem)
            return adapter.render_content_core().strip()
        except Exception:
            return ''

    def are_headers_ordered(self, html):
        if html:
            dom = fromstring(html)
            last = 1
            for el in dom.cssselect('h1,h2,h3,h4,h5,h6'):
                idx = int(el.tag[-1])
                if idx - last > 1:
                    # means they skipped from say h1 -> h5
                    # h1 -> h2 is allowed
                    return False
                last = idx
        return True

    def __call__(self):
        html = self.html
        self.request.response.setHeader('Content-type', 'application/json')
        return json.dumps({
            'title': self.context.Title(),
            'id': self.context.getId(),
            'description': self.context.Description(),
            'linksValid': self.are_links_valid,
            'headersOrdered': self.are_headers_ordered(html),
            'html': html_parser.unescape(html),
            'isTemplate': self.context in get_template_repository_info()['templates'],
            # 'containsBackendUrls': self.contains_backend_urls,
        })


class PageLayoutSelector(BrowserView):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        action = self.request.form.get('action')
        if action == 'save':
            data = self.save()
        else:
            data = self.get()
        return json.dumps(data)

    def save(self):
        adapted = ILayoutAware(self.context)
        data = self.request.form.get('data')
        if not data:
            return
        data = json.loads(data)
        adapted.pageSiteLayout = data['page_layout']
        adapted.sectionSiteLayout = data['section_layout']
        parent = aq_parent(self.context)
        if ISiteRoot.providedBy(parent):
            # check if default page...
            if getDefaultPage(parent) == self.context.id:
                # also set site wide global layout setting...
                registry = getUtility(IRegistry)
                field = registry_field.TextLine(title=u'Default layout', required=False)
                new_record = Record(field)
                registry.records['castle.cms.default_layout'] = new_record
                registry['castle.cms.default_layout'] = data['section_layout']
        return {
            'success': True
        }

    def get(self):
        available = dict([(t.value, t.title)
                          for t in AvailableSiteLayouts(self.context)])
        applied = 'index.html'
        applied_context = getSite()

        context = self.context
        adapted = context_adapted = ILayoutAware(context)
        selected = adapted.pageSiteLayout
        if selected is None:
            context = aq_parent(context)
            while not ISiteRoot.providedBy(context):
                adapted = ILayoutAware(context, None)
                if adapted and adapted.sectionSiteLayout:
                    selected = adapted.sectionSiteLayout
                    break
                context = aq_parent(context)

        if selected:
            applied = selected
            applied_context = context

        return {
            'success': True,
            'available': available,
            'applied': applied,
            'context': utils.get_path(self.context),
            'applied_context': utils.get_path(applied_context),
            'page_layout': context_adapted.pageSiteLayout,
            'section_layout': context_adapted.sectionSiteLayout,
            'folder': IDexterityContainer.providedBy(self.context)
        }


class PublishContent(BrowserView):

    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        try:
            state = api.content.get_state(obj=self.context)
        except WorkflowException:
            state = 'published'
        if state != 'published':
            api.content.transition(self.context, 'publish')
        return json.dumps({
            'success': True
        })


class i18njs(i18n.i18njs):

    def __call__(self, domain='widgets', language='en'):
        return super(i18njs, self).__call__(domain, language)


class PingCurrentDraft(BrowserView):
    """
    To add to the current draft modified time
    """

    def __call__(self):
        draft = getCurrentDraft(self.request, create=False)
        if draft is not None:
            draft._p_changed = 1


class ContentBody(BrowserView):
    def __call__(self):
        self.request.response.setHeader('Content-type', 'application/json')
        cutils = Utils(self.context, self.request)
        data = {
            'title': self.context.title,
            'id': self.context.id,
            'has_image': utils.has_image(self.context),
            'youtube_url': None
        }
        rendered = None
        if self.context.portal_type in ('Image',):
            pass
        elif self.context.portal_type == 'Video':
            fi = getattr(self.context, 'file', None)
            data.update({
                'youtube_url': cutils.get_youtube_url(self.context),
                'content_type': getattr(
                    fi, 'original_content_type', getattr(fi, 'contentType', None))
            })
        else:
            feed = SearchFeed(api.portal.get())
            adapter = queryMultiAdapter((self.context, feed), IFeedItem)
            if adapter is not None:
                rendered = adapter.render_content_core().strip()
        return json.dumps({
            'portal_type': self.context.portal_type,
            'url': self.context.absolute_url(),
            'data': data,
            'rendered': rendered
        })
