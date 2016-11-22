from plone.memoize.view import memoize
from plone.app.theming.utils import theming_policy
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone.browser.main_template import MainTemplate as BaseMainTemplate
from castle.cms.theming import isPloneTheme


class MainTemplate(BaseMainTemplate):
    _ajax_template = ViewPageTemplateFile('templates/ajax_main_template.pt')
    _main_template = ViewPageTemplateFile('templates/main_template.pt')

    @property
    @memoize
    def is_castle_theme(self):
        policy = theming_policy(self.request)
        settings = policy.getSettings()
        if settings is None:
            return False
        if not policy.isThemeEnabled():
            return False
        if not isPloneTheme(settings):
            return True
        return False

    @property
    def ajax_template(self):
        if self.is_castle_theme:
            return self._ajax_template
        return BaseMainTemplate.ajax_template

    @property
    def main_template(self):
        if self.is_castle_theme:
            return self._main_template
        return BaseMainTemplate.main_template
