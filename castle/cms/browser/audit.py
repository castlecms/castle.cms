import csv

from cStringIO import StringIO
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.resources import add_resource_on_request
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility

from castle.cms import audit
from castle.cms.indexing.hps import gen_query
from castle.cms.indexing.hps import health_is_good
from castle.cms.indexing.hps import hps_get_data
from castle.cms.indexing.hps import is_enabled as hps_is_enabled


class AuditView(BrowserView):
    label = 'My Activity Log'
    limit = 50
    user = True

    inner_template = ViewPageTemplateFile('templates/audit-inner.pt')
    error_template = ViewPageTemplateFile('templates/audit-error.pt')

    def __call__(self):
        # utility function to add resource to rendered page
        add_resource_on_request(self.request, 'castle-components-audit')

        self._user_cache = {}
        self.site_path = '/'.join(self.context.getPhysicalPath())
        try:
            self.results, self.total, _ = self.do_query()

            if 'Export' in self.request.form.get('export', ''):
                return self.export(data=self.results)
        except Exception:
            self.inner_template = self.error_template
        return super(AuditView, self).__call__()

    def render_inner(self):
        return self.inner_template()

    def get_user(self, userid):
        if not userid:
            return
        if userid in self._user_cache:
            return self._user_cache[userid]
        user = api.user.get(userid)
        if user is not None:
            self._user_cache[userid] = user
        return user

    @property
    def can_connect_to_index(self):
        if not hps_is_enabled():
            return False

        return health_is_good()

    def get_obj(self, uid):
        return uuidToObject(uid)

    def get_path(self, data):
        path = data.get('path')
        if not path:
            return ''
        if path.startswith(self.site_path):
            return path[len(self.site_path):]
        return path

    def get_query(self):
        form = self.request.form

        if self.user:
            user = api.user.get_current().getId().lower()
        else:
            user = form.get('user', '').lower()

        if len(user.strip()) <= 0:
            user = None

        query = gen_query(
            typeval=form.get("type", None),
            user=user,
            content=form.get('content', None),
            after=form.get('after', None),
            before=form.get('before', None))

        return query

    def export(self, data=None):
        if data is None:
            index_name = audit.get_index_name()
            query = self.get_query()
            data, _, _ = hps_get_data(index_name, query, sort='date:desc', size=3000)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Action', 'Path', 'User', 'Summary', 'Date'])
        for result in data:
            rowdata = result['_source']
            writer.writerow([
                rowdata['name'],
                self.get_path(rowdata),
                rowdata['user'],
                rowdata['summary'],
                rowdata['date']
            ])
        output.seek(0)

        resp = self.request.response
        resp.setHeader('Content-Disposition', 'attachment; filename=export.csv')
        resp.setHeader('Content-Type', 'text/csv')
        return output.read()

    def do_query(self):
        index_name = audit.get_index_name()
        query = self.get_query()

        try:
            page = int(self.request.get('page', 1))
        except Exception:
            page = 1
        start = (page - 1) * self.limit

        results = hps_get_data(index_name, query, sort='date:desc', from_=start, size=self.limit)

        return results
