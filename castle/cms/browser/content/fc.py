from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from Acquisition import aq_inner
from Acquisition import aq_parent
from castle.cms import cache
from castle.cms import tasks
from castle.cms import trash
from castle.cms.utils import get_paste_data
from castle.cms.utils import is_max_paste_items
from OFS.CopySupport import _cb_encode
from OFS.CopySupport import cookie_path
from OFS.CopySupport import CopyError
from OFS.Moniker import Moniker
from plone import api
from plone.app.content.browser.contents import FolderContentsView as BaseFolderContentsView
from plone.app.content.browser.contents import copy
from plone.app.content.browser.contents import cut
from plone.app.content.browser.contents import delete
from plone.app.content.browser.contents import paste
from plone.app.content.browser.contents import rename
from plone.app.content.interfaces import IStructureAction
from plone.locking.interfaces import ILockable
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.log import logger
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from uuid import uuid4
from ZODB.POSException import ConflictError
from zope.component import getMultiAdapter
from zope.container.interfaces import INameChooser
from zope.event import notify
from zope.interface import implementer
from zope.lifecycleevent import ObjectModifiedEvent
from re import sub

from plone.app.content.browser.vocabulary import (
    VocabularyView,
    VocabLookupException,
    _parseJSON,
    _unsafe_metadata,
    _safe_callable_metadata,
    translate,
    safe_unicode,
    json_dumps,
    itertools,
)

import json
import transaction


try:
    from plone.app.content.browser.vocabulary import DEFAULT_PERMISSION_SECURE
except ImportError:
    DEFAULT_PERMISSION_SECURE = 'Modify portal content'


class CutActionView(cut.CutActionView):
    def finish(self):
        oblist = []
        for ob in self.oblist:
            if ob.wl_isLocked():
                self.errors.append(_(u'${title} is being edited and cannot be cut.',
                                     mapping={u'title': self.objectTitle(ob)}))
                continue
            if not ob.cb_isMoveable():
                self.errors.append(_(u'${title} is being edited and can not be cut.',
                                     mapping={u'title': self.objectTitle(ob)}))
                continue
            m = Moniker(ob)
            oblist.append(m.dump())
        if len(oblist) > 20 and cache.redis_installed():
            cache_key = str(uuid4())
            cache.set(cache_key, oblist, expire=60 * 60 * 24)
            cp = (1, [['cache:' + cache_key]])
        else:
            cp = (1, oblist)
        cp = _cb_encode(cp)
        resp = self.request.response
        resp.setCookie('__cp', cp, path='%s' % cookie_path(self.request))
        self.request['__cp'] = cp


class CopyActionView(copy.CopyActionView):
    def action(self, obj):
        folder_path = '/'.join(obj.getPhysicalPath())
        trash = self.catalog(path={'query': folder_path}, trashed=True)
        if len(trash):
            path = trash[0].getPath()
            self.errors.append(_(u'Please restore or permanently delete recycled \
                contents before copying a folder: {path}'.format(path=path)))
        else:
            super(CopyActionView, self).action(obj)

    def finish(self):
        oblist = []
        for ob in self.oblist:
            if not ob.cb_isCopyable():
                self.errors.append(_(u'${title} cannot be copied.',
                                     mapping={u'title': self.objectTitle(ob)}))
                continue
            m = Moniker(ob)
            oblist.append(m.dump())
        if len(oblist) > 20 and cache.redis_installed():
            cache_key = str(uuid4())
            cache.set(cache_key, oblist, expire=60 * 60 * 24)
            cp = (0, [['cache:' + cache_key]])
        else:
            cp = (0, oblist)
        cp = _cb_encode(cp)
        resp = self.request.response
        resp.setCookie('__cp', cp, path='%s' % cookie_path(self.request))
        self.request['__cp'] = cp


class PasteActionView(paste.PasteActionView):

    def paste_async(self, paste_data):
        self.errors = ['']
        self.failure_msg = """You have selected to paste %i items which is a large amount.
This action can take a long time to accomplish. We will email you
when the content is done being moved.""" % paste_data['count']
        tasks.paste_items.delay(
            self.request.form['folder'], paste_data['op'],
            paste_data['mdatas'])
        return self.json({
            'status': 'success',
            'msg': {
                'label': 'INFO',
                'text': self.failure_msg
            }
        })

    def copy_error(self):
        self.errors = ['']
        self.failure_msg = """There was an error pasting the data. It's possible
the number of items you have selected is larger than what the browser allows.
Try pasting a smaller number of items."""
        return self.json({
            'status': 'failure',
            'msg': {
                'label': 'WARNING',
                'type': 'warning',
                'text': self.failure_msg
            }
        })

    def __call__(self):
        try:
            paste_data = get_paste_data(self.request)
        except CopyError:
            return self.copy_error()
        if is_max_paste_items(paste_data):
            return self.paste_async(paste_data)

        return super(PasteActionView, self).__call__()


class DeleteActionView(delete.DeleteActionView):

    delete_warning = """
<div class="portalMessage error">
<b>WARNING</b>:
<p>You have selected to delete %i items which is a large amount.
This action can take a long time to accomplish. We will email you
when the content is done being deleted.</p>
<p>
<b>Link integrity checks can not be done on delete this large of a batch.</b>
</p>
</div>"""

    failure_msg_template = """
You have selected to delete %i items which is a large amount.
This action can take a long time to accomplish. We will email you
when the content is done being deleted."""

    def delete_async(self, uids, count):
        self.errors = ['']
        self.failure_msg = self.failure_msg_template % count
        tasks.delete_items.delay(uids)
        return self.json({
            'status': 'success',
            'msg': {
                'label': 'WARNING',
                'type': 'warning',
                'text': self.failure_msg
            }
        })

    def action(self, obj):
        parent = obj.aq_inner.aq_parent

        lockable = ILockable(obj, None)
        if lockable and lockable.locked():
            lockable.clear_locks()

        try:
            parent.manage_delObjects(obj.getId(), self.request)
        except Unauthorized:
            self.errors.append(
                _(u'You are not authorized to delete ${title}.',
                    mapping={u'title': self.objectTitle(self.dest)}))

    def __call__(self):
        selection = self.get_selection()
        over = False
        count = len(selection)
        if count < 100:
            catalog = api.portal.get_tool('portal_catalog')
            paths = []
            for brain in catalog(UID=selection):
                paths.append(brain.getPath())
            count = len(catalog(path={'query': paths, 'depth': -1}))
            if count > 100:
                over = True
        else:
            over = True

        if not over:
            return super(DeleteActionView, self).__call__()

        # special handling from here on so we can do async handling
        if self.request.form.get('render') == 'yes':
            self.request.response.setHeader('Content-Type', 'application/json')
            return json.dumps({
                'html': self.delete_warning % count
            })
        else:
            return self.delete_async(selection, count)


class TrashActionView(delete.DeleteActionView):
    success_msg = 'Successfully moved items to recycle bin'
    failure_msg = 'Failed to move items to recycle bin'

    def action(self, obj):
        trash.object(obj)


@implementer(IStructureAction)
class TrashAction(delete.DeleteAction):

    template = ViewPageTemplateFile('templates/fc-trash.pt')
    order = 4

    def get_options(self):
        return {
            'title': 'Recycle bin',
            'id': 'recycle',
            'icon': 'trash',
            'context': 'default',
            'url': self.context.absolute_url() + '/@@fc-trash',
            'form': {
                'title': 'Move selected items to recycle bin',
                'submitText': 'Yes',
                'submitContext': 'danger',
                'template': self.template(),
                'closeText': 'No',
                'dataUrl': self.context.absolute_url() + '/@@fc-trash'
            }
        }


class RenameActionView(rename.RenameActionView):
    success_msg = _('Items renamed')
    failure_msg = _('Failed to rename all items')

    def __call__(self):
        self.errors = []
        self.protect()
        context = aq_inner(self.context)

        catalog = getToolByName(context, 'portal_catalog')
        mtool = getToolByName(context, 'portal_membership')

        missing = []
        for key in self.request.form.keys():
            if not key.startswith('UID_'):
                continue
            index = key.split('_')[-1]
            uid = self.request.form[key]
            brains = catalog(UID=uid)
            if len(brains) == 0:
                missing.append(uid)
                continue
            obj = brains[0].getObject()
            title = self.objectTitle(obj)
            if not mtool.checkPermission('Copy or Move', obj):
                self.errors(_(u'Permission denied to rename ${title}.',
                              mapping={u'title': title}))
                continue

            sp = transaction.savepoint(optimistic=True)

            newid = self.request.form['newid_' + index].encode('utf8')
            newtitle = self.request.form['newtitle_' + index]

            lockable = ILockable(obj, None)
            if lockable:
                lockable.clear_locks()

            try:
                obid = obj.getId()
                title = obj.Title()
                change_title = newtitle and title != newtitle
                if change_title:
                    getSecurityManager().validate(obj, obj, 'setTitle',
                                                  obj.setTitle)
                    obj.setTitle(newtitle)
                    notify(ObjectModifiedEvent(obj))
                if newid and obid != newid:
                    parent = aq_parent(aq_inner(obj))
                    # Make sure newid is safe
                    newid = INameChooser(parent).chooseName(newid, obj)
                    # Update the default_page on the parent.
                    context_state = getMultiAdapter(
                        (obj, self.request), name='plone_context_state')
                    if context_state.is_default_page():
                        parent.setDefaultPage(newid)
                    parent.manage_renameObjects((obid, ), (newid, ))
                elif change_title:
                    # the rename will have already triggered a reindex
                    obj.reindexObject()
            except ConflictError:
                raise
            except Exception as e:
                sp.rollback()
                logger.error(u'Error renaming "{title}": "{exception}"'.format(
                    title=title.decode('utf8'), exception=e))
                self.errors.append(_(u'Error renaming ${title}', mapping={
                    'title': title.decode('utf8')}))

        return self.message(missing)


# override the layout so it only shows the folder contents
FC_MINIMAL_LAYOUT = """<!doctype html>
<html class="no-js" lang="en-us" data-gridsystem="bs3">
  <head>
    <meta charset="utf-8" />

    <link data-tile="${portal_url}/@@castle.cms.metadata"/>

    <link data-tile="${portal_url}/@@plone.app.standardtiles.stylesheets"/>

    <meta name="generator" content="Castle - https://www.wildcardcorp.com"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  </head>
  <body id="visual-portal-wrapper">
    <div data-tile="${context_url}/@@plone.app.standardtiles.toolbar" />

      <!-- Main Content -->
      <div class="row" id="main-content-container">
        <div id="main-content">
            ${structure: content.main}
        </div>
      </div>

      <link data-tile="${portal_url}/@@plone.app.standardtiles.javascripts"/>
  </body>
</html>
"""


class FolderContentsView(BaseFolderContentsView):
    capital_following_lowercase_pattern = r'([a-z])([A-Z])'
    hyphen_or_underscore_pattern = r'[_-]'
    non_capitalized_word_pattern = r'([a-zA-Z])([a-z]+)'

    def __call__(self):
        self.request.environ['X-CASTLE-LAYOUT'] = FC_MINIMAL_LAYOUT
        return super(FolderContentsView, self).__call__()

    def un_camel_case(self, string):
        return sub(
            self.capital_following_lowercase_pattern,
            r"\1 \2",
            string,
        )

    def remove_hyphens_and_underscores(self, string):
        return sub(
            self.hyphen_or_underscore_pattern,
            ' ',
            string,
        )

    def capitalize(self, string, title_case=False):
        '''
        We use this function instead of just using str.capitalize() and str.title()
        becasue we don't want to change words with multiple sequential capital letters,
        such as UID
        '''
        pattern = '{}{}'.format(
            '' if title_case else '^',
            self.non_capitalized_word_pattern,
        )
        return sub(
            pattern,
            lambda match: '{}{}'.format(match.group(1).upper(), match.group(2)),
            string,
        )

    def get_normalized_column_name(self, column_name, title_case=True):
        formatted_name = self.remove_hyphens_and_underscores(column_name)
        formatted_name = self.un_camel_case(formatted_name)
        return self.capitalize(formatted_name, title_case)

    def get_columns(self):
        columns = super(FolderContentsView, self).get_columns()
        sm = getSecurityManager()
        if sm.checkPermission(DEFAULT_PERMISSION_SECURE, self.context):
            # if has permission, add more more columns
            columns.update({
                'Creator': 'Creator',
                'last_modified_by': 'Last modified by'
            })
        for column_key, column_name in columns.items():
            columns[column_key] = self.get_normalized_column_name(column_name)
        return columns

    def get_options(self):
        options = super(FolderContentsView, self).get_options()
        options['vocabularyUrl'] = '{}/all_contents_vocab?name=plone.app.vocabularies.Catalog'.format(
            options['upload']['baseUrl']
        )
        return options


class AllContentsVocabView(VocabularyView):
    def __call__(self):
        """
        All of this to remove two lines. Sigh.
        Another reason functions shouldn't be 4000 lines long
        """
        context = self.get_context()
        self.request.response.setHeader(
            'Content-Type', 'application/json; charset=utf-8'
        )

        try:
            vocabulary = self.get_vocabulary()
        except VocabLookupException as error:
            return json_dumps({'error': error.message})

        results_are_brains = False
        if hasattr(vocabulary, 'search_catalog'):
            query = self.parsed_query()
            results = vocabulary.search_catalog(query)
            results_are_brains = True
        elif hasattr(vocabulary, 'search'):
            try:
                query = self.parsed_query()['SearchableText']['query']
            except KeyError:
                results = iter(vocabulary)
            else:
                results = vocabulary.search(query)
        else:
            results = vocabulary

        try:
            total = len(results)
        except TypeError:
            total = 0

        # get batch
        batch = _parseJSON(self.request.get('batch', ''))
        if batch and ('size' not in batch or 'page' not in batch):
            batch = None  # batching not providing correct options
        if batch:
            page = int(batch['page'])
            size = int(batch['size'])
            start = (max(page - 1, 0)) * size
            end = start + size
            try:
                results = results[start:end]
            except TypeError:
                results = itertools.islice(results, start, end)

        # build result items
        items = []

        attributes = _parseJSON(self.request.get('attributes', ''))
        if isinstance(attributes, basestring) and attributes:
            attributes = attributes.split(',')

        translate_ignored = self.get_translated_ignored()
        if attributes:
            base_path = self.get_base_path(context)
            sm = getSecurityManager()
            can_edit = sm.checkPermission(DEFAULT_PERMISSION_SECURE, context)
            for vocab_item in results:
                if not results_are_brains:
                    vocab_item = vocab_item.value
                item = {}
                for attr in attributes:
                    key = attr
                    if ':' in attr:
                        key, attr = attr.split(':', 1)
                    if attr in _unsafe_metadata and not can_edit:
                        continue
                    if key == 'path':
                        attr = 'getPath'
                    val = getattr(vocab_item, attr, None)
                    if callable(val):
                        if attr in _safe_callable_metadata:
                            val = val()
                        else:
                            continue
                    if key == 'path':
                        val = val[len(base_path):]
                    if (
                        key not in translate_ignored and
                        isinstance(val, basestring)
                    ):
                        item[key] = translate(
                            _(safe_unicode(val)),
                            context=self.request
                        )
                    else:
                        item[key] = val
                items.append(item)
        else:
            for item in results:
                items.append({'id': item.value, 'text': item.title})

        if total == 0:
            total = len(items)

        return json_dumps({
            'results': items,
            'total': total
        })
