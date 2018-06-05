from Products.Five.browser import BrowserView
import subprocess
import redis
import celery
import celery.bin.base
import celery.bin.celery
import celery.platforms


class StatusView(BrowserView):

    def docsplit(self):
        retval = self.DocsplitSearch()
        if retval[0]:
            status = 'OK'
            icon = '<span class="glyphicon glyphicon-ok" aria-hidden="true"></span> Docsplit: '
            return '<span>' + icon + status + '</span>'
        if not retval[0]:
            status = 'ERROR: ' + retval[1]
            icon = '<span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Docsplit: '
            return '<span>' + icon + status + '</span>'

    def elasticsearch(self):
        rs = redis.Redis("localhost")
        try:
            rs.get(None)
            status = 'OK'
            icon = '<span class="glyphicon glyphicon-ok" aria-hidden="true"></span> Redis: '
        except redis.ConnectionError as e:
            status = 'ERROR: ' + str(e)
            icon = '<span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Redis: '
        return '<span>' + icon + status + '</span>'

    def celery(self):
        app = celery.Celery('tasks', broker='redis://')
        status = celery.bin.celery.CeleryCommand.commands['status']()
        status.app = status.get_app()
        try:
            status.run()
            check = 'OK'
            icon = '<span class="glyphicon glyphicon-ok" aria-hidden="true"></span> Celery: '
        except celery.bin.base.Error as e:
            check = "ERROR: " + str(e)
            icon = '<span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Celery: '
        except redis.ConnectionError:
            check = "ERROR: Celery cannot connect to redis"
            icon = '<span class="glyphicon glyphicon-remove" aria-hidden="true"></span> Celery: '
        return '<span>' + icon + check + '</span>'

    def DocsplitSearch(self):
        try:
            subprocess.check_call('docsplit')
            return True, 'ok'
        except OSError as e:
            return False, str(e)
