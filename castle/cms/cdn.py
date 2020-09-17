class cdn(object):

    def __init__(self, hostname=[], port=80, path=''):
        self.hostname = hostname
        self.port = port
        self.path = path

    def process_url(self, url, relative_path=''):

        # splits url parts
        protocol, path = url.split('://')
        path = path.split('/')
        hostname = self.hostname[0]
        if self.port not in [80, ]:
            hostname = '%s:%s' % (hostname, self.port)

        path[0] = hostname
        # add path, if supplied
        if self.path:
            path.insert(1, self.path)

        # join everything
        path = '/'.join(path)
        url = '%s://%s' % (protocol, path)
        return url
