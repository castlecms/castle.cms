import json
import logging
import math
import os
import shutil
import tempfile
import time

from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms import commands
from castle.cms import utils
from castle.cms.browser.utils import Utils
from castle.cms.commands import exiftool
from castle.cms.files import duplicates
from castle.cms.interfaces import ITrashed
from castle.cms.utils import get_upload_fields
from castle.cms.utils import publish_content
from lxml.html import fromstring
from OFS.interfaces import IFolder
from OFS.ObjectManager import checkValidId
from persistent.dict import PersistentDict
from plone import api
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
        if self.request.form.get('action') == 'check':
            return self.check()
        elif self.request.form.get('action') == 'create':
            return self.create()
        elif self.request.form.get('action') == 'remove':
            return self.remove_file_content()
        elif self.request.form.get('action') == 'chunk-upload':
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

        cache_key_prefix = '%s-uploads-' % '/'.join(self.context.getPhysicalPath()[1:])
        if chunk == 1:
            # initializing chunk upload

            _id = utils.get_random_string(50)
            filename = self.request.form['name']
            tmp_dir = tempfile.mkdtemp()
            tmp_filename = os.path.join(tmp_dir, filename)
            info = {
                'last_chunk': 1,
                'total_size': total_size,
                'chunk_size': chunk_size,
                'tmp_file': tmp_filename,
                'name': filename
            }
        else:
            info = cache.get(cache_key_prefix + _id)
            # check things are matching up
            if info['last_chunk'] != chunk - 1:
                raise Exception('Invalid chunk sequence')
            if info['total_size'] != total_size:
                raise Exception('Invalid total size')
            if info['chunk_size'] != chunk_size:
                raise Exception('Inconsistent chunk size')
            info['last_chunk'] = chunk

        mode = 'wb'
        if chunk > 1:
            # appending to file now
            mode = 'ab+'
            if not os.path.exists(info['tmp_file']):
                raise Exception('No tmp upload file found')
        fi = open(info['tmp_file'], mode)

        while True:
            data = self.request.form['file'].read(2 << 16)
            if not data:
                break
            fi.write(data)
        fi.close()

        if chunk == total_chunks:
            # finish upload
            dup = False
            if not existing_id:
                try:
                    obj = self.create_file_content(info)
                except duplicates.DuplicateException as ex:
                    obj = ex.obj
                    dup = True
            else:
                try:
                    info['existing_id'] = existing_id
                    info['field_name'] = field_name
                    obj, success, msg = self.update_file_content(info)
                    if not success:
                        self.update_file_content(info)
                        self._clean_tmp(info)
                        return json.dumps({
                            'success': False,
                            'id': _id,
                            'reason': msg
                        })
                except Exception:
                    logger.warning(
                        'Failed to update content.', exc_info=True)
                    self._clean_tmp(info)
                    return json.dumps({
                        'success': False,
                        'id': _id
                    })
            if not info.get('field_name', '').startswith('tmp_'):
                # tmp files need to stick around and be managed later...
                self._clean_tmp(info)
            cache.delete(cache_key_prefix + _id)
            return dump_object_data(obj, dup)
        else:
            cache.set(cache_key_prefix + _id, info)
            check_put = None
            while check_put is None:
                try:
                    check_put = cache.get(cache_key_prefix + _id)
                except Exception:
                    cache.set(cache_key_prefix + _id, info)
        return json.dumps({
            'success': True,
            'id': _id
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
        if (aspect and (
                aspect.getConstrainTypesMode() != 1 or
                [type_] != aspect.getImmediatelyAddableTypes())):
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
        if (type_ in ('Image', 'File', 'Video', 'Audio') and
                exiftool is not None and 'tmp_file' in info):
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
        return form.get('selectedType[typeId]',
                        form.get('selectedType[id]')).replace('%20', ' ')

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
            pt = portal_types[type_id]
            add_perm = utils.get_permission_title(pt.add_permission)

            if valid and not self.can_add(folder, type_id):
                valid = False
                self.status = 'You are not allowed to add this content type here'
            elif valid and not self.sm.checkPermission(add_perm, folder):
                valid = False
                self.status = 'You do not have permission to add content here.'
            elif valid and self.request.form['id'] in folder.objectIds():
                valid = False
                ob = folder[self.request.form['id']]
                if ITrashed.providedBy(ob):
                    self.status = ('Content in recycling bin with same id exists. '
                                   'Delete, rename or restore recycled content to use this.')
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


class QualityCheckContent(BrowserView):

    def __call__(self):

        valid = True
        for link in getOutgoingLinks(self.context):
            state = api.content.get_state(obj=link.to_object, default='published')
            if state != 'published':
                valid = False
                break

        headers_ordered = True

        try:
            feed = SearchFeed(api.portal.get())
            adapter = queryMultiAdapter((self.context, feed), IFeedItem)
            html = adapter.render_content_core().strip()
        except Exception:
            html = ''

        if html:
            dom = fromstring(html)
            last = 1
            for el in dom.cssselect('h1,h2,h3,h4,h5,h6'):
                idx = int(el.tag[-1])
                if idx - last > 1:
                    # means they skipped from say h1 -> h5
                    # h1 -> h2 is allowed
                    headers_ordered = False
                    break
                last = idx

        self.request.response.setHeader('Content-type', 'application/json')
        return json.dumps({
            'title': self.context.Title(),
            'id': self.context.getId(),
            'description': self.context.Description(),
            'linksValid': valid,
            'headersOrdered': headers_ordered,
            'html': html_parser.unescape(html)
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
