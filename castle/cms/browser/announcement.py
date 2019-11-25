from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from zope.component import getUtility
import json


class FirstVisitMessage(BrowserView):
    def __call__(self):
        registry = getUtility(IRegistry)
        displayMsg = registry.get("castle.show_disclaimer")

        self.request.response.setHeader('Content-type', 'application/json')

        result = {
            "enabled": displayMsg
        }

        if displayMsg:
            result["msg"] = registry.get("castle.site_disclaimer")

        return json.dumps(result)
