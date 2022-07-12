import os
import subprocess

import celery.bin.celery
import opensearchpy
import redis
from collective.celery.utils import getCelery
from wildcard.hps.opensearch import WildcardHPSCatalog
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView


class StatusView(BrowserView):

    def docsplit(self):
        try:
            subprocess.check_call('docsplit')
            return True, 'ok'
        except OSError as e:
            return False, str(e)

    def redis(self):
        server = os.environ.get("REDIS_SERVER", "127.0.0.1:6379")
        host, _, port = server.partition(':')
        if not host or not port:
            return '[{}] {}'.format(server, 'Invalid configuration')

        client = redis.StrictRedis(
            host=host, port=int(port), db=0,
            socket_timeout=0.5, socket_connect_timeout=0.5)
        try:
            client.client_list()
            return True, '[{}] ok'.format(server)
        except redis.ConnectionError as e:
            return False, '[{}] {}'.format(server, str(e))

    def celery(self):
        app = getCelery()
        status = celery.bin.celery.CeleryCommand.commands['status']()
        status.app = app
        try:
            status.run()
            return True, 'ok'
        except Exception as e:
            return False, str(e)

    def wildcardhps(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        hpscatalog = WildcardHPSCatalog(catalog)
        conn = hpscatalog.connection
        try:
            (conn.cluster.health())
            return True, 'ok'
        except opensearchpy.ConnectionError as e:
            return False, str(e)
