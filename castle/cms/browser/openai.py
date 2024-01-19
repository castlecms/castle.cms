from Products.Five import BrowserView
from plone.protect import (
    PostOnly,
    protect,
)
from plone import api
import requests
import random
import json

class OpenAI(BrowserView):

    @protect(PostOnly)
    def __call__(self, REQUEST=None):
        data = self.request.form.get("data", {})
        return json.dumps(self.openai_api_request(data))

    def openai_api_request(self, data):
        response = requests.post(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps({
                "model": "gpt-3.5-turbo",
                "messages": [{
                    "role": "user",
                    "content": data,
                }],
                "temperature": 0.2,
                "max_tokens": 500,
            }),
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(self.api_key)
            },
        )
        return self.handle_response(response)

    def handle_response(self, response, num_retries=1, delay=1, max_retries=10):
        if not response.ok:
            try:
                response_json = response.json()
            except:  # noqa
                return self.error_response()
            error = response_json.get("error", {})
            code = error.get("code", {})
            if response.status_code == 429 and code != "insufficient_quota":  # nosec
                if num_retries <= max_retries:
                    self.exponential_backoff(data=self.request.data, num_retries=num_retries, delay=delay)
        try:
            received_data = response.json()
        except:  # noqa
            return self.error_response()

        status_code = response.status_code
        success = 200 <= status_code < 300

        if success:
            status = "success"
            message = received_data.get('choices')[0].get('message').get('content')
        else:  # openai api error
            status = response_json.get("error", {}).get("code", {})
            message = received_data.get("error", {}).get("message", {})

        return_data = {
            "status": status,
            "message": message,
        }

        response = self.request.response
        response.setStatus(status_code)
        response.setHeader('Content-Type', 'application/json')

        return return_data

    def error_response(self):  # unforseen error
        response = self.request.response
        response.setStatus(response.status_code)
        response.setHeader('Content-Type', 'application/json')
        return {
            "status": "error",
            "message": "unforseen error",
        }

    @property
    def api_key(self):
        key = api.portal.get_registry_record("castle.openai_api_key", default="default_value")
        return key

    def exponential_backoff(self, data, num_retries, delay, exponential_base=2):
        num_retries = num_retries + 1
        delay *= exponential_base * (2 * random.random())  # nosec
        self.openai_api_request(data=data, num_retries=num_retries, delay=delay)
