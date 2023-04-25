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
            scheduled = ins.scheduled()
        except Exception:
            scheduled = ''
        try:
            reserved = ins.reserved()
        except Exception:
            reserved = ''
        try:
            stats = ins.stats()
        except Exception:
            stats = ''
        try:
            registered = ins.registered()
        except Exception:
            registered = ''
        try:
            report = ins.report()
            for worker in report.keys():
                clean_info = report[worker]['ok'].replace('\'', '').replace('\"', '').replace(' \n', '').replace('\n ', '')
                while True:
                    alpha = len(clean_info)
                    clean_info = clean_info.replace('  ', ' ')
                    beta = len(clean_info)
                    if alpha>beta:
                        pass
                    else:
                        break
                clean_info = clean_info.split('\n')
                while True:
                    try:
                        index = clean_info.index('')
                        clean_info.pop(index)
                    except:
                        report[worker] = clean_info
                        break
        except Exception as e:
            report = ''
        types = [[registered, "registered"], [reserved, "reserved"], [active, "active"], [scheduled, "scheduled"]]
        counts = {}
        for _type in types:
            count = 0
            keys = _type[0].keys()
            try:
                for key in keys:
                    if _type[1] == "stats":
                        count += len(_type[0][key].get('total'))
                    else:
                        count += len(_type[0][key])
                counts[_type[1]]=count
            except Exception:
                counts[_type[1]]=0
        return {
            'workers': ping,
            'active': active,
            'scheduled': scheduled,
            'reserved': reserved,
            'stats': stats,
            'registered': registered,
            'counts': counts,
            'report': report,
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
