import json
import logging
import plone.api as api
import re


logger = logging.getLogger('castle.cms')


class BackendUrlUtils(object):
    # start of string
    # optional http:// or https:// is catured as 'protocol'
    # optional leading slashes are captured as 'leading_slashes'
    # everything else is captured as 'url'
    URL_PATTERN = r'^(?P<protocol>https?:\/\/)?(?P<leading_slashes>\/+)?(?P<url>.*)$'
    UNSET = object()
    _public_url = UNSET
    _backend_urls = UNSET
    _invalid_backend_urls = ['a']

    @property
    def backend_urls(self):
        if getattr(self, '_backend_urls', self.UNSET) is self.UNSET:
            formatted_backend_urls = []
            backend_urls = api.portal.get_registry_record('plone.backend_url', default=[]) or []
            for backend_url in backend_urls:
                formatted_url = self.get_formatted_url(backend_url)
                if formatted_url and isinstance(formatted_url, basestring):
                    formatted_backend_urls.append(formatted_url)
            self._backend_urls = formatted_backend_urls
        return self._backend_urls

    @property
    def public_url(self):
        if getattr(self, '_public_url', self.UNSET) is self.UNSET:
            public_url = api.portal.get_registry_record('plone.public_url', default=None) or None
            if public_url and isinstance(public_url, basestring):
                self._public_url = public_url
            else:
                self._public_url = None
        return self._public_url

    @property
    def invalid_backend_urls(self):
        # if a site has the same backend and public url, do not consider it invalid
        if getattr(self, '_invalid_backend_urls', self.UNSET) is self.UNSET:
            public_url = self.public_url
            backend_urls = self.backend_urls
            if public_url is None:
                self._invalid_backend_urls = backend_urls
            else:
                self._invalid_backend_urls = [
                    backend_url
                    for backend_url in backend_urls
                    if backend_url != public_url
                ]
        return self._invalid_backend_urls

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


class HasBackendUrlView(BackendUrlUtils):

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
