import json
import logging
import plone.api as api
import re


logger = logging.getLogger('castle.cms')


class HasBackendUrlView(object):
    # start of string
    # optional http:// or https:// is catured as 'protocol'
    # optional leading slashes are captured as 'leading_slashes'
    # everything else is captured as 'url'
    URL_PATTERN = r'^(?P<protocol>https?:\/\/)?(?P<leading_slashes>\/+)?(?P<url>.*)$'

    @property
    def backend_urls(self):
        formatted_backend_urls = []
        backend_urls = api.portal.get_registry_record('plone.backend_url', default=[]) or []
        for backend_url in backend_urls:
            formatted_url = self.get_formatted_url(backend_url)
            if formatted_url and isinstance(formatted_url, basestring):
                formatted_backend_urls.append(formatted_url)
        return formatted_backend_urls

    @property
    def public_url(self):
        public_url = api.portal.get_registry_record('plone.public_url', default=None) or None
        if public_url and isinstance(public_url, basestring):
            return public_url
        return None

    @property
    def invalid_backend_urls(self):
        # if a site has the same backend and public url, do not consider it invalid
        public_url = self.public_url
        backend_urls = self.backend_urls
        if public_url is None:
            return backend_urls
        return [
            backend_url
            for backend_url in backend_urls
            if backend_url != public_url
        ]

    def get_formatted_url(self, url):
        try:
            # probably the only way to not get a match here is a non-string
            match = re.match(self.URL_PATTERN, url)
            return match.groupdict()['url']
        except Exception:
            return None

    def get_invalid_backend_urls_found(self, content):
        return [
            invalid_backend_url
            for invalid_backend_url in self.invalid_backend_urls
            if invalid_backend_url in content
        ]

    def check_document(self):
        if api.user.is_anonymous():
            return 'must be authenticated'
        self.request.response.setHeader('Content-type', 'application/json')
        try:
            data = self.request.form.get('data', '')
            try:
                data = data.decode('utf-8')
            except Exception:
                logger.warn('could not decode data with utf-8')
            invalid_backend_urls = self.get_invalid_backend_urls_found(data)
            if len(invalid_backend_urls) == 0:
                return_data = {'error': False}
            else:
                logger.warn('There were backend urls found in the html')
                logger.info('Backend urls found:')
                logger.info(invalid_backend_urls)
                logger.info('Data searched for: ' + self.request.URL)
                return_data = {
                    'error': True,
                    'message': 'There were backend urls found in the html',
                }

        except Exception:
            return_data = {
                'error': True,
                'message': 'Unknown error while checking for backend urls in the html',
            }
        finally:
            return json.dumps(return_data)
