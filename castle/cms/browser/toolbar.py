from castle.cms.utils import is_mosaic_edit_form
from plone.app.layout.viewlets import toolbar
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class ToolbarViewletManager(toolbar.ToolbarViewletManager):
    """
    so we can provide info on user tasks
    """

    custom_template = ViewPageTemplateFile('templates/toolbar.pt')

    @property
    def show(self):
        if (self.portal_state.anonymous() or
                self.request.form.get('VIEW_AS_ANONYMOUS_VIEW') == 'true'):
            return False

        if is_mosaic_edit_form(self.request):
            return False
        return True
