from Products.Five import BrowserView
from celery.task.control import inspect
from plone import api
from castle.cms import taskinfo


class CeleryControlPanel(BrowserView):

    def info(self):
        ins = inspect()
        try:
            ping = ins.ping()
        except Exception:
            ping = ''
        try:
            active = ins.active()
        except Exception:
            active = ''
        try:
            reserved = ins.reserved()
        except Exception:
            reserved = ''
        try:
            stats = ins.stats()
        except Exception:
            stats = ''
        return {
            'workers': ping,
            'active': active,
            'reserved': reserved,
            'stats': stats
        }

    def get_task_name(self, _id):
        return taskinfo.get_task_name(_id)

    def task_info(self, task):
        info = taskinfo.get_info(task)
        on_site = False
        if info['kwargs'].get('site_path') == '/'.join(self.site.getPhysicalPath()):
            on_site = True

        obj_path = ''
        obj = None
        args = info['args']
        if len(args) > 0 and isinstance(args[0], basestring):
            obj_path = args[0].replace('object://', '')
            obj = self.site.unrestrictedTraverse(str(obj_path), None)

        info.update({
            'on_site': on_site,
            'obj': obj,
            'obj_path': obj_path,
        })
        return info

    def __call__(self):
        self.site = api.portal.get()
        return self.index()
