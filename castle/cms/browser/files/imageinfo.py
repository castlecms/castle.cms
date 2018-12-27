import json
from Products.Five.browser import BrowserView
from castle.cms import utils


class ImageInfoView(BrowserView):

    def __call__(self):
        response = self.request.response
        response.setHeader("Content-type", "application/json")
        return json.dumps(utils.get_image_info(self.context))
