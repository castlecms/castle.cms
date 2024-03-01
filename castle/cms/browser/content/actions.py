from OFS.CopySupport import CopyError
from zope.component import queryMultiAdapter
from plone.locking.interfaces import ILockable
from Acquisition import aq_inner
from Acquisition import aq_parent
from castle.cms import tasks
from castle.cms import trash
from castle.cms.browser.utils import Utils
from castle.cms.tasks.template import move_to_templates
from castle.cms.tasks.template import copy_to_templates
from castle.cms.utils import get_paste_data
from castle.cms.utils import is_max_paste_items
from castle.cms.utils import get_template_repository_info
from castle.cms.tasks.email import send_email_reminder
from plone.app.content.browser import actions
from plone.app.workflow.browser import sharing
from plone.app.workflow.events import LocalrolesModifiedEvent
from plone.memoize.view import memoize
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage

from z3c.form import button
from z3c.form import field
from z3c.form import form
from z3c.form.widget import ComputedWidgetAttribute
from zope.interface import Interface

import plone.api as api
import sys
import zope.schema as schema
from zope.event import notify
from zExceptions import Forbidden


class ObjectPasteView(actions.ObjectPasteView):

    def paste_async(self, paste_data):
        folder_path = '/'.join(self.context.getPhysicalPath())
        site_path = '/'.join(api.portal.get().getPhysicalPath())
        folder_path = folder_path[len(site_path):]
        tasks.paste_items.delay(
            folder_path, paste_data['op'],
            paste_data['mdatas'])
        return self.do_redirect(
            self.canonical_object_url,
            """You have selected to paste %i items which is a large amount.
This action can take a long time to accomplish. We will email you
when the content is done being moved.""" % paste_data['count'],
            'error'
        )

    def do_action(self):
        paste_data = get_paste_data(self.request)
        if is_max_paste_items(paste_data):
            return self.paste_async(paste_data)
        return super(ObjectPasteView, self).do_action()


class RenameForm(actions.RenameForm):
    template = ViewPageTemplateFile('templates/object_rename.pt')

    @button.buttonAndHandler(_(u'Rename'), name='Rename')
    def handle_rename(self, action):
        lockable = ILockable(self.context)
        if lockable:
            lockable.clear_locks()
        return super(RenameForm, self).handle_rename(self, action)


def is_locked(view):
    locking_view = queryMultiAdapter(
        (view.context, view.request), name='plone_lock_info')

    return locking_view is not None and locking_view.is_locked()


class DeleteConfirmationForm(actions.DeleteConfirmationForm):

    template = ViewPageTemplateFile('templates/delete_confirmation.pt')

    @property
    @memoize
    def items_to_delete(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        results = catalog({
            'path': '/'.join(self.context.getPhysicalPath())
        })
        return len(results)

    def more_info(self):
        if self.items_to_delete > 120:
            IStatusMessage(self.request).add("""
You have selected to delete %i items which is a large amount.
This action can take a long time to accomplish. We will email you
when the content is done being deleted.""" % self.items_to_delete, 'error')
        else:
            return super(DeleteConfirmationForm, self).more_info()

    @property
    def is_locked(self):
        return is_locked(self)

    @button.buttonAndHandler(_(u'Delete'), name='Delete')
    def handle_delete(self, action):
        title = safe_unicode(self.context.Title())
        parent = aq_parent(aq_inner(self.context))

        # has the context object been acquired from a place it should not have
        # been?
        if self.context.aq_chain == self.context.aq_inner.aq_chain:
            if self.items_to_delete > 120:
                tasks.delete_items.delay([IUUID(self.context)])
                IStatusMessage(self.request).add("""
You have selected to delete %i items which is a large amount.
This action can take a long time to accomplish. We will email you
when the content is done being deleted.""" % self.items_to_delete, 'error')
            else:
                if self.is_locked:
                    # force unlock before delete...
                    lockable = ILockable(self.context)
                    lockable.clear_locks()

                parent.manage_delObjects(self.context.getId(), self.request)
                IStatusMessage(self.request).add(
                    _(u'${title} has been deleted.', mapping={u'title': title}))
        else:
            IStatusMessage(self.request).add(
                _(u'"${title}" has already been deleted',
                  mapping={u'title': title})
            )

        self.request.response.redirect(parent.absolute_url())

    @property
    def items_to_trash(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        putils = getToolByName(self.context, 'plone_utils')
        results = catalog({
            'path': '/'.join(self.context.getPhysicalPath()),
            'portal_type': putils.getUserFriendlyTypes(),
        })
        return len(results)

    @button.buttonAndHandler(u'Move to recycle bin', name='Move')
    def handle_move(self, action):
        title = safe_unicode(self.context.Title())
        parent = aq_parent(aq_inner(self.context))

        # has the context object been acquired from a place it should not have
        # been?
        if self.context.aq_chain == self.context.aq_inner.aq_chain:
            trash.object(self.context)
            IStatusMessage(self.request).add(u'%s has been moved to recycle bin.' % title)

        self.request.response.redirect(parent.absolute_url())

    @button.buttonAndHandler(u'Cancel', name='Cancel')
    def handle_cancel(self, action):
        utils = Utils(self.context, self.request)
        target = utils.get_object_url(self.context)
        return self.request.response.redirect(target)


class ObjectCutView(actions.ObjectCutView):

    def do_action(self):
        if is_locked(self):
            # force unlock before delete...
            lockable = ILockable(self.context)
            lockable.clear_locks()

        try:
            self.parent.manage_cutObjects(self.context.getId(), self.request)
        except CopyError:
            return self.do_redirect(
                self.view_url,
                _(
                    u'${title} is not moveable.',
                    mapping={'title': self.title},
                ),
            )

        return self.do_redirect(
            self.view_url,
            _(
                u'${title} cut.',
                mapping={'title': self.title},
            ),
            'info',
        )


class ConvertToFolderForm(form.Form):

    label = 'Convert to Folder'
    description = (
        '"Convert to Folder" will change the id of the current page, '
        'create a folder with the id and title of the original page, '
        'move the current page inside the new folder, '
        'and assign the original page as the default view of the new folder, '
        'so that the new folder will display the same way the page used to, '
        'but will now be able to be used as a folder as well. '
    )

    @button.buttonAndHandler(u'Convert To Folder', name='Convert')
    def handle_convert(self, action):
        original_page = self.context
        original_page_id = original_page.id
        original_page_title = original_page.title
        default_page_id = original_page_id + '_default_page'
        api.content.rename(original_page, default_page_id)
        original_parent = aq_parent(aq_inner(original_page))
        new_folder = api.content.create(
            original_parent,
            type='Folder',
            title=original_page_title,
            id=original_page_id,
        )
        api.content.move(original_page, new_folder)
        new_folder.setDefaultPage(default_page_id)
        IStatusMessage(self.request).add(u'Conversion complete')
        return self.do_redirect(new_folder)

    @button.buttonAndHandler(u'Cancel', name='Cancel')
    def handle_cancel(self, action):
        return self.do_redirect(self.context)

    def do_redirect(self, context):
        utils = Utils(self.context, self.request)
        target = utils.get_object_url(context)
        return self.request.response.redirect(target)


class IMakeTemplateForm(Interface):

    template_title = schema.TextLine(
        description=(
            u'The title for the new template. This will be used when selecting a template from the template list'
        ),
        title=u'Template Title',
        required=True,
    )


default_template_title = ComputedWidgetAttribute(
    lambda form: form.context.Title(),
    field=IMakeTemplateForm['template_title'],
)


class TemplateForm(form.Form):
    can_create_template = False
    new_template_title = None
    fields = field.Fields(IMakeTemplateForm)
    template = ViewPageTemplateFile('templates/convert_template.pt')
    ignoreContext = True
    label = _(
        'heading_convert_template',
        default='Make a Template',
    )
    description = _(
        'description_convert_template',
        default=(
            '"Move To Template Repository" will move current item to "Template Repository" '
            'folder, while "Copy to Template Repository" will keep current item in place '
            'and create a copy in the Template Repository folder.'
        ),
    )

    @property
    def status_messages(self):
        return IStatusMessage(self.request)

    def get_template_titles(self):
        return [
            getattr(template, 'Title', lambda: None)()
            for template in get_template_repository_info()['templates']
        ]

    def get_conversion_message(self, is_copy=False):
        action_text = 'copied as' if is_copy else 'converted to'
        return (
            u'{title} has been {action_text} a template, and is now available '
            u'to use from the Add Content screen (in the templates tab)'
        ).format(
            title=self.new_template_title,
            action_text=action_text,
        )

    def prepare_template_creation(self):
        data, errors = self.extractData()
        if not errors:
            template_title = data.get('template_title', None)
            if template_title is None or template_title in self.get_template_titles():
                self.status_messages.add(
                    'Template NOT created. There is already a template '
                    'with this title. Choose a different title.'
                )
                self.request.response.redirect(self.context.absolute_url())
                return
            self.new_template_title = template_title
            self.can_create_template = True

    @button.buttonAndHandler(_(u'Move To Template Repository'), name='move')
    def handle_move_to_templates(self, action):
        self.prepare_template_creation()
        if self.can_create_template:
            template_object = move_to_templates(self.context, self.new_template_title)

            if template_object is not None:
                self.status_messages.add(self.get_conversion_message(False))
                redirect_url = get_template_repository_info()['folder_url'] + '/folder_contents'
                return self.request.response.redirect(redirect_url)

    @button.buttonAndHandler(_(u'Copy To Template Repository'), name='copy')
    def handle_copy_to_templates(self, action):
        self.prepare_template_creation()
        if self.can_create_template:
            template_object = copy_to_templates(self.context, self.new_template_title)
            if template_object is not None:
                self.status_messages.add(self.get_conversion_message(True))
                return self.do_redirect(self.context)

    @button.buttonAndHandler(u'Cancel', name='cancel')
    def handle_cancel(self, action):
        return self.do_redirect(self.context)

    def do_redirect(self, context):
        utils = Utils(self.context, self.request)
        target = utils.get_object_url(context)
        return self.request.response.redirect(target)


class SharingView(sharing.SharingView):

    def __call__(self):

        postback = self.handle_form()
        if postback:
            # Reset python recursion limit to baseline if previously raised
            sys.setrecursionlimit(1000)
            return self.template()
        else:
            context_state = self.context.restrictedTraverse(
                "@@plone_context_state")
            url = context_state.view_url()
            self.request.response.redirect(url)

    def large_count(self):
        """
        Displays an alert indicating that we're operating in a view
        with a high document count, which slows down the process of
        granting permissions.
        """

        try:
            event = LocalrolesModifiedEvent(self.context, self.request)
            obj = event.object
            if obj._count:
                return True if obj._count.value > 1000 else False
        except AttributeError:
            return False

    def handle_form(self):
        """
        Overrides the 'handle_form' method so we can temporarily increase
        the python recursion limit if needed.

        Also sends a notification email to individual users assigned to a page.
        """
        postback = True

        # print('=== actors ===')
        # actors = []
        # rt = api.portal.get_tool("portal_repository")
        # history = rt.getHistoryMetadata(self.context)
        # for i in range(history.getLength(countPurged=False)):
        #     data = history.retrieve(i, countPurged=False)
        #     actor = data["metadata"]["sys_metadata"]["principal"]
        #     actors.append(actor) if actor not in actors else None
        # print(actors)

        # print('=== contributors ===')
        # assigned_users = []

        # acl_users = api.portal.get_tool('acl_users')
        # local_roles = acl_users._getLocalRolesForDisplay(self.context)

        # for name, rolesm, rtype, rid in local_roles:
        #     print(name)
        #     print(rolesm)
        #     print(rtype)
        #     assigned_users.append(name)
        # print(assigned_users)

        form = self.request.form
        submitted = form.get('form.submitted', False)
        save_button = form.get('form.button.Save', None) is not None
        cancel_button = form.get('form.button.Cancel', None) is not None
        if submitted and save_button and not cancel_button:
            if not self.request.get('REQUEST_METHOD', 'GET') == 'POST':
                raise Forbidden

            authenticator = self.context.restrictedTraverse('@@authenticator',
                                                            None)
            if not authenticator.verify():
                raise Forbidden
            
            event = LocalrolesModifiedEvent(self.context, self.request)
            obj = event.object
            try:
                if obj._count.value > 1000:
                    # XXX: We're increasing the recursion limit here to prevent the
                    # 'maximum recursion depth exceeded' error thrown by 'cPickle' 
                    # that occurs when granting permissions in a large directory 
                    # (i.e. the 'image-directory')
                    sys.setrecursionlimit(2000)  
            except AttributeError:
                # User search form submitted, no need to get count
                pass

            # Update the acquire-roles setting
            if self.can_edit_inherit():
                inherit = bool(form.get('inherit', False))
                reindex = self.update_inherit(inherit, reindex=False)
            else:
                reindex = False

            # Update settings for users and groups
            entries = form.get('entries', [])
            roles = [r['id'] for r in self.roles()]

            settings = []
            for entry in entries:
                assigned_roles=[r for r in roles if entry.get('role_%s' % r, False)]
                settings.append(
                    dict(id=entry['id'],
                         type=entry['type'],
                         roles=assigned_roles))

                if entry['type'] == 'user' and 'Reviewer' in assigned_roles:
                    # Only send emails to individual users assigned as 'Reviewers'
                    user = api.user.get(entry['id'])
                    email = user.getProperty('email')
                    if email:
                        data = dict(
                            uid=user.getId(),
                            name=user.getProperty('fullname') or user.getId(),
                            email=email,
                            roles=roles,
                        )
                        send_email_reminder.delay(obj, data)

            if settings:
                reindex = self.update_role_settings(settings, reindex=False) \
                            or reindex
            if reindex:
                self.context.reindexObjectSecurity()
                notify(LocalrolesModifiedEvent(self.context, self.request))
            IStatusMessage(self.request).addStatusMessage(
                _(u"Changes saved."), type='info')
            
        # Other buttons return to the sharing page
        if cancel_button:
            postback = False

        return postback
