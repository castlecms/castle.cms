from Products.Five.browser import BrowserView
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
        if x[0]:
            return x
        if not x[0]:
            return x

    def elasticsearch(self):
        r = redis.Redis()
        try:
            r.client_list()
            x = True, 'ok'
        except redis.ConnectionError as e:
            x = False, str(e)
        if x[0]:
            return x
        if not x[0]:
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
            x = False, str(d)
        if x[0]:
            return x
        else:
            return x
