from Products.Five import BrowserView
from plone import api
import json


class FinishView(BrowserView):

    def __call__(self):
        # XXX this should be an ajax view

        if api.user.is_anonymous():
            return self.request.response.redirect(self.context.absolute_url())

        portal_memberdata = api.portal.get_tool('portal_memberdata')
        if not portal_memberdata.hasProperty("tours_viewed"):
            portal_memberdata.manage_addProperty(
                id="tours_viewed", value=[], type="lines")

        self.request.response.setHeader('Content-type', 'application/json')
        user = api.user.get_current()

        viewed = list(user.getProperty('tours_viewed', []))
        if not viewed:
            viewed = []
        viewed.append(self.request.form.get('tour'))
        viewed = list(set(viewed))
        user.setMemberProperties(mapping={'tours_viewed': viewed})
        return json.dumps({
            'success': True
        })


class TourAgainView(BrowserView):

    def __call__(self):
        if api.user.is_anonymous():
            return self.request.response.redirect(self.context.absolute_url())

        user = api.user.get_current()
        user.setMemberProperties(mapping={'tours_viewed': []})
        return self.request.response.redirect(self.context.absolute_url())
