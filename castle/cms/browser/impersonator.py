from castle.cms import impersonator
from plone import api
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import NotFound
from zope.component import getMultiAdapter


class ImpersonatorView(BrowserView):
    index = ViewPageTemplateFile('templates/impersonate.pt')

    def __call__(self):
        resp = self.request.response
        return_url = self.request.form.get('return_url')
        if not return_url:
            return_url = self.context.absolute_url()
        if self.request.form.get('action') == 'stop':
            resp.expireCookie(impersonator.COOKIE_NAME)
            return resp.redirect(return_url)
        elif self.request.REQUEST_METHOD == 'POST':
            authenticator = getMultiAdapter((self.context, self.request),
                                            name=u"authenticator")
            if authenticator.verify():
                resp.setCookie(impersonator.COOKIE_NAME, self.request.form.get('username'))
                return resp.redirect(return_url)

        if api.user.is_anonymous():
            raise NotFound()
        return self.index()
