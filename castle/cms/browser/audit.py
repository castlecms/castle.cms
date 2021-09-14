from castle.cms import audit
from castle.cms.utils import ESConnectionFactoryFactory
from cStringIO import StringIO
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.resources import add_resource_on_request
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility

import csv


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
            results = self.do_query()
            self.results = results['hits']['hits']
            self.total = results['hits']['total']

            if 'Export' in self.request.form.get('export', ''):
                return self.export()
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
    def el_connected(self):
        registry = getUtility(IRegistry)
        if not registry.get('collective.elasticsearch.interfaces.IElasticSettings.enabled', False):
            return False
        es = ESConnectionFactoryFactory()()
        try:
            return es.cluster.health()['status'] in ('green', 'yellow')
        except Exception:
            return False

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
        filters = []
        form = self.request.form
        if form.get('type'):
            filters.append(
                {'term': {'type': form.get('type')}}
            )
        if self.user:
            filters.append(
                {'term': {'user': api.user.get_current().getId()}}
            )
        else:
            if form.get('user'):
                filters.append(
                    {'term': {'user': form.get('user')}}
                )
        if form.get('content'):
            items = form.get('content').split(';')
            cqueries = []
            for item in items:
                cqueries.append({'term': {'object': item}})
            filters.append(
                {'or': cqueries}
            )
        if form.get('after'):
            filters.append(
                {'range': {'date': {'gte': form.get('after')}}}
            )
        if form.get('before'):
            filters.append(
                {'range': {'date': {'lte': form.get('before')}}}
            )
        if len(filters) == 0:
            query = {
                "query": {'match_all': {}}
            }
        else:
            if len(filters) > 1:
                qfilter = {'and': filters}
            else:
                qfilter = filters[0]
            query = {
                "query": {
                    'filtered': {
                        'filter': qfilter,
                        'query': {'match_all': {}}
                    }
                }
            }
        return query

    def export(self):
        index_name = audit.get_index_name()
        es = ESConnectionFactoryFactory()()
        query = self.get_query()
        results = es.search(
            index=index_name,
            doc_type=audit.es_doc_type,
            body=query,
            sort='date:desc',
            size=3000)
        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(['Action', 'Path', 'User', 'Summary', 'Date'])
        for result in results['hits']['hits']:
            data = result['_source']
            writer.writerow([
                data['name'],
                self.get_path(data),
                data['user'],
                data['summary'],
                data['date']
            ])

        resp = self.request.response
        resp.setHeader('Content-Disposition', 'attachment; filename=export.csv')
        resp.setHeader('Content-Type', 'text/csv')
        output.seek(0)
        return output.read()

    def do_query(self):
        index_name = audit.get_index_name()
        es = ESConnectionFactoryFactory()()
        query = self.get_query()

        try:
            page = int(self.request.get('page', 1))
        except Exception:
            page = 1
        start = (page - 1) * self.limit
        results = es.search(
            index=index_name,
            doc_type=audit.es_doc_type,
            body=query,
            sort='date:desc',
            from_=start,
            size=self.limit)

        return results
