from castle.cms import tasks
from zExceptions import Forbidden
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.workflow import PloneMessageFactory as _
from plone.app.workflow.events import LocalrolesModifiedEvent
from zope.event import notify

import plone.api as api


"""
Overrides the form submit in the '@@sharing' view.
This allows us to defer the action of granting image
permissions to a separate thread (which is necessary for
views that contain thousands of images like 'image-repository').

"""
def handle_form(self):
    postback = True

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
            settings.append(
                dict(id=entry['id'],
                        type=entry['type'],
                        roles=[r for r in roles
                        if entry.get('role_%s' % r, False)]))
        if settings:
            reindex = self.update_role_settings(settings, reindex=False) \
                        or reindex
        if reindex:
            # This runs successfully, albeit slowly
            self.context.reindexObjectSecurity()

            # This fails
            notify(LocalrolesModifiedEvent(self.context, self.request))

            # tasks.grant_permissions.delay()
        IStatusMessage(self.request).addStatusMessage(
            _(u"Changes saved."), type='info')

    # Other buttons return to the sharing page
    if cancel_button:
        postback = False

    return postback