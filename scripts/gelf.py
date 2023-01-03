import logging
import json
import os
import socket
import time

import requests


logger = logging.getLogger(__name__)


# GELFHandler copied from castle.cms.gelf -- copied here so that castle.cms doesn't have
# to be installed into the same virtualenv/python environment as scripts that need to
# use just the GELFHandler, and possibly use it in a python 3.9 context.
_dummy_log_record = logging.LogRecord('foobar', 20, 'foobar', None, None, None, None)
IGNORED_LOG_ATTRIBUTES = [a for a in _dummy_log_record.__dict__.keys()] + ['message']

class GELFHandler(logging.Handler):
    def __init__(self, timeout=300, *args, **kwargs):
        super(GELFHandler, self).__init__(*args, **kwargs)

        self.request_timeout = timeout

    @property
    def url(self):
        return os.getenv("GELF_URL", None)

    @property
    def hostname(self):
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    def emit(self, record, **kwargs):
        if self.url is None:
            logger.error(
                "GELF_URL environment variable needs to be configured to log with "
                "GELFHanlder")
            return

        try:
            short_message = self.format(record)

            full_message = {}
            for name in record.__dict__.keys():
                # ignored attributes are, basically, default attributes of a standard LogRecord
                # as well as the 'message'
                if name not in IGNORED_LOG_ATTRIBUTES:
                    full_message[name] = record.__dict__[name]

            timestamp = int(time.time())
            if 'timestamp' in full_message:
                try:
                    timestamp = int(full_message['timestamp'])
                    del full_message['timestamp']
                except Exception:
                    logger.error(
                        "could get valid timestamp from full_message for GELFHandler",
                        exc_info=True)

            msg = {
                "version": "1.1",
                "host": self.hostname,
                "full_message": full_message,
                "short_message": short_message,
                "level": record.levelno,
                "timestamp": timestamp,
            }

            resp = requests.post(
                self.url,
                data=json.dumps(msg),
                headers={"Content-Type": "application/json"},
                timeout=self.request_timeout)
            if resp.status_code < 200 or resp.status_code >= 300:
                logger.error("GELF endpoint rejecting log: (HTTP {}) {}\n\nMessage:\n{}".format(
                    resp.status_code,
                    resp.content,
                    self.format(record)))
        except Exception:
            logger.error("failed to process log message to GELF url.\n\nMessage:\n{}".format(
                self.format(record)), exc_info=True)



