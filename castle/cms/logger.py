from ZServer.medusa import http_server

import App
import logging
import time


logger = logging.getLogger('castle.cms')

try:
    server = App.config.getConfiguration().servers[0]
except Exception:
    server = None


def medua_log_request(medusa_request, bytes):
    """
    we are patching default logging to disable so we can use our better
    logging with the actual request ob...
    """
    pass


http_server.http_request.log = medua_log_request


def log_date_string(when):
    logtime = time.localtime(when)
    return time.strftime('%d/', logtime) + \
           http_server.http_date.monthname[logtime[1]] + \
           time.strftime('/%Y:%H:%M:%S ', logtime) + \
           http_server.tz_for_log


def log_request(request):
    if server is not None:
        try:
            user = request['AUTHENTICATED_USER']
        except (KeyError, TypeError):
            user = None

        user_name = user
        try:
            user_name = user.name
        except AttributeError:
            try:
                user_name = user.getUserName()
            except AttributeError:
                pass

        if not user_name:
            user_name = 'Anonymous User'

        origin = request.environ['REMOTE_ADDR']
        if request.get_header('x-forwarded-for'):
            forwarded = request.get_header('x-forwarded-for')
            forwarded = forwarded.split(',')[-1].strip()
            if forwarded:
                origin = forwarded

        url = request.environ['PATH_INFO']
        if request.environ.get('QUERY_STRING'):
            url += '?' + request.environ.get('QUERY_STRING')
        request_info = '{} {} {}'.format(
            request.REQUEST_METHOD,
            url,
            request.environ['SERVER_PROTOCOL']
        )

        user_agent = request.get_header('user-agent') or ''
        referer = request.get_header('referer') or ''

        resp = request.response
        server.logger.log(
            origin,
            '- %s [%s] "%s" %d %s "%s" "%s"\n' % (
                user_name,
                log_date_string(time.time()),
                request_info,
                resp.getStatus(),
                resp.headers.get('content-length', '0'),
                referer,
                user_agent
                )
            )
