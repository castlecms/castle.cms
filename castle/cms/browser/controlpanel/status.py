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
            return True
        if not retval[0]:
            return False
        
    def DocsplitSearch(self):
        try:
            subprocess.check_call('docsplit')
            return True, 'ok'
        except OSError as e:
            return False, str(e)

    def docsplitError(self):
        retval2 = self.DocsplitSearch()
        if not retval2[0]:
            return str(retval2[1])

    def elasticsearchCheck(self):
        r = redis.Redis()
        try:
            r.client_list()
            return True, 'ok'
        except redis.ConnectionError as e:
            return False, str(e)

    def elasticsearch(self):
        retval = self.elasticsearchCheck()
        if retval[0]:
            return True
        if not retval[0]:
            return False

    def elasticsearchError(self):
        retval = self.elasticsearchCheck()
        if retval[0]:
            return True
        if not retval[0]:
            return retval[1]

    def celery(self):
        retval = self.CeleryChecker()
        if retval[0]:
            return True
        if not retval[0]:
            return False

    def celeryError(self):
        retval2 = self.CeleryChecker()
        if 'node' in retval2[1]:
            return retval2[1]
        else:
            return 'Cannot connect to Redis'

    def CeleryChecker(self):
        app = celery.Celery('tasks', broker='redis://')
        status = celery.bin.celery.CeleryCommand.commands['status']()
        status.app = status.get_app()
        try:
            status.run()
            return True, "ok"
        except celery.bin.base.Error as e:

            return False, str(e)
        except redis.ConnectionError as d:

            return False, str(d)
