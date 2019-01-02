from OFS.CopySupport import CopyError
from zope.component import queryMultiAdapter
from plone.locking.interfaces import ILockable
from Acquisition import aq_inner
from Acquisition import aq_parent
from castle.cms import tasks
from castle.cms import trash
from castle.cms.browser.utils import Utils
from castle.cms.utils import get_paste_data
from castle.cms.utils import is_max_paste_items
from plone import api
from plone.app.content.browser import actions
from plone.memoize.view import memoize
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button


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
            return self.do_redirect(self.view_url,
                                    _(u'${title} is not moveable.',
                                        mapping={'title': self.title}))

        return self.do_redirect(
            self.view_url,
            _(u'${title} cut.', mapping={'title': self.title}),
            'info'
        )
