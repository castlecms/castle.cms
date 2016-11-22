from ZPublisher.BaseRequest import quote


_protocol_headers = (
    'HTTP_X_FORWARDED_PROTO',
    'HTTP_X_FORWARDED_PROTOCOL',
    'HTTP_X_SCHEME'
)


def _get_protocol(req):
    for header in _protocol_headers:
        if header in req.environ:
            return req.environ[header]
    return 'http'


def traversal(self, client, request, response=None):
    """
    This is a copy of
    Products.SiteAccess.VirtualHostMonster.VirtualHostMonster.__call__
    with tweaks for:
        1. better detect protocol
        2. better detect host name

    with the ability to already map domains, better predicting http vs https
    and host names is mostly all we need here...
    """
    vh_used = 0
    stack = request['TraversalRequestNameStack']
    path = None

    # detect forwarded for host, port, scheme automatically
    protocol = _get_protocol(request)
    host = request['SERVER_URL'].split('://')[1].lower()
    host, _, port = request.environ.get('HTTP_HOST', host).partition(':')
    port = port or None
    if port:
        server_url = '{}://{}:{}'.format(protocol, host, port)
    else:
        server_url = '{}://{}'.format(protocol, host)

    if server_url != request.SERVER_URL:
        request.setServerURL(protocol, host, port)
        stack_path = stack[:]
        stack_path.reverse()
        request['VIRTUAL_URL_PARTS'] = vup = (
            request['SERVER_URL'], quote('/'.join(stack_path)))
        request['VIRTUAL_URL'] = '/'.join(vup)

        # new ACTUAL_URL
        add = (stack_path and
               request['ACTUAL_URL'].endswith('/')) and '/' or ''
        request['ACTUAL_URL'] = request['VIRTUAL_URL'] + add

    while 1:
        if stack and stack[-1] == 'VirtualHostBase':
            vh_used = 1
            stack.pop()
            protocol = stack.pop()
            host = stack.pop()
            if ':' in host:
                host, port = host.split(':')
                request.setServerURL(protocol, host, port)
            else:
                request.setServerURL(protocol, host)
            path = list(stack)

        # Find and convert VirtualHostRoot directive
        # If it is followed by one or more path elements that each
        # start with '_vh_', use them to construct the path to the
        # virtual root.
        vh = -1
        for ii in range(len(stack)):
            if stack[ii] == 'VirtualHostRoot':
                vh_used = 1
                pp = ['']
                at_end = (ii == len(stack) - 1)
                if vh >= 0:
                    for jj in range(vh, ii):
                        pp.insert(1, stack[jj][4:])
                    stack[vh:ii + 1] = ['/'.join(pp), self.id]
                    ii = vh + 1
                elif ii > 0 and stack[ii - 1][:1] == '/':
                    pp = stack[ii - 1].split('/')
                    stack[ii] = self.id
                else:
                    stack[ii] = self.id
                    stack.insert(ii, '/')
                    ii += 1
                path = stack[:ii]
                # If the directive is on top of the stack, go ahead
                # and process it right away.
                if at_end:
                    request.setVirtualRoot(pp)
                    del stack[-2:]
                break
            elif vh < 0 and stack[ii][:4] == '_vh_':
                vh = ii

        if vh_used or not self.have_map:
            if path is not None:
                path.reverse()
                vh_part = ''
                if path and path[0].startswith('/'):
                    vh_part = path.pop(0)[1:]
                if vh_part:
                    request['VIRTUAL_URL_PARTS'] = vup = (
                        request['SERVER_URL'],
                        vh_part, quote('/'.join(path)))
                else:
                    request['VIRTUAL_URL_PARTS'] = vup = (
                        request['SERVER_URL'], quote('/'.join(path)))
                request['VIRTUAL_URL'] = '/'.join(vup)

                # new ACTUAL_URL
                add = (path and
                       request['ACTUAL_URL'].endswith('/')) and '/' or ''
                request['ACTUAL_URL'] = request['VIRTUAL_URL'] + add

            return

        vh_used = 1  # Only retry once.
        # Try to apply the host map if one exists, and if no
        # VirtualHost directives were found.

        if self.sub_map:
            return

        host = request['SERVER_URL'].split('://')[1].lower()
        hostname, port = (host.split(':', 1) + [None])[:2]
        ports = self.fixed_map.get(hostname, 0)
        if not ports:
            get = self.sub_map.get
            while hostname:
                ports = get(hostname, 0)
                if ports:
                    break
                if '.' not in hostname:
                    return
                hostname = hostname.split('.', 1)[1]
        elif ports:
            pp = ports.get(port, 0)
            if pp == 0 and port is not None:
                # Try default port
                pp = ports.get(None, 0)
            if not pp:
                return
            # If there was no explicit VirtualHostRoot, add one at the end
            if pp[0] == '/':
                pp = pp[:]
                pp.insert(1, self.id)
            stack.extend(pp)
