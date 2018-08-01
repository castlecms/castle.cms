from Products.Five.browser import BrowserView
from elasticsearch import Elasticsearch
import elasticsearch
import subprocess
import redis
import celery
import celery.bin.base
import celery.bin.celery
import celery.platforms


class StatusView(BrowserView):

    def docsplit(self):
        try:
            subprocess.check_call('docsplit')
            x = True, 'ok'
        except OSError as e:
            x = False, str(e)
        return x

    def redis(self):
        r = redis.Redis("localhost")
        try:
            r.client_list()
            x = True, 'ok'
        except redis.ConnectionError as e:
            x = False, str(e)
        return x

    def celery(self):
        app = celery.Celery('tasks', broker='redis://')
        status = celery.bin.celery.CeleryCommand.commands['status']()
        status.app = status.get_app()
        try:
            status.run()
            x = True, 'ok'
        except celery.bin.base.Error as e:
            x = False, str(e)
        except redis.ConnectionError as d:
            x = False, 'Cannot connect to Redis'
        return x

    def elasticsearch(self):
        es = Elasticsearch()
        try:
            (es.cluster.health())
            x = True, 'ok'
        except elasticsearch.ConnectionError as e:
            x = False, str(e)
        return x

