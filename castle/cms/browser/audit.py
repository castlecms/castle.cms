"""
Environment Variables:

# see castle.cms.audit
CASTLE_CMS_AUDIT_LOG_INSTANCE

# we assume all logs are submitted to the same index per-instance
# we assume that specific site audit logs can be fetched by including
#   'schema_type', 'schema_version', 'instance', and 'site' as attributes
#   to the search query to this index
CASTLE_CMS_AUDIT_LOG_INDEXNAME

# if audit logs records are coming from a opensearch index that was populated
# by, eg, castle.cms.gelf.GELFHandler, then the log data will be key's on
# an attribute like 'full_message' in the _source results
CASTLE_CMS_AUDIT_LOG_FIELD_MAP_PREFIX

# opensearch connections are made using the WildcardHPSCatalog object,
# ultimately, but do not necessarily sit on the same instance of opensearch,
# and therefore the connection settings used for the audit log have a
# different prefix, which is AUDIT_OPENSEARCH_ instead of just OPENSEARCH_
#
# see wildcard.hps.opensearch for the details of the connection settings
AUDIT_OPENSEARCH_*

"""
import csv
from cStringIO import StringIO
import logging
import os

from plone import api
from plone.app.uuid.utils import uuidToObject
from Products.CMFPlone.resources import add_resource_on_request
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from castle.cms import audit
from castle.cms.indexing.hps import gen_audit_query
from castle.cms.indexing.hps import health_is_good
from castle.cms.indexing.hps import hps_get_data
from castle.cms.indexing.hps import is_enabled as hps_is_enabled


logger = logging.getLogger("Plone")


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
            logger.error("problem with querying hps", exc_info=True)
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
    def field_map_prefix(self):
        return os.getenv("CASTLE_CMS_AUDIT_LOG_FIELD_MAP_PREFIX", None)

    @property
    def can_connect_to_index(self):
        if not hps_is_enabled(foraudit=True):
            return False

        return health_is_good(foraudit=True)

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

        try:
            site_path = '/'.join(api.portal.get().getPhysicalPath())
        except api.exc.CannotGetPortalError:
            site_path = '(zoperoot)'

        query = gen_audit_query(
            field_map_prefix=self.field_map_prefix,
            sort="date",
            sortdir="desc",
            instance=os.getenv("CASTLE_CMS_AUDIT_LOG_INSTANCE"),
            site=site_path,
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
            data, _, _ = hps_get_data(index_name, query, foraudit=True, size=3000)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Action', 'Path', 'User', 'Summary', 'Date'])
        for rowdata in data:
            writer.writerow([
                rowdata["actionname"],
                self.get_path(rowdata),
                rowdata["user"],
                rowdata["summary"],
                rowdata["date"]
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

        results = hps_get_data(index_name, query, foraudit=True, from_=start, size=self.limit)

        # process results into something a little less complex to handle within the template
        finalresults = []
        for result in results[0]:
            data = result['_source']
            # IE if the data is coming from a index that had it's content generated by
            # castle.cms.gelf.GELFHandler, then the stored object would actually have
            # a full_message field, which then has the various audit log fields
            if self.field_map_prefix is not None:
                data = data[self.field_map_prefix]
            finalresults.append(data)

        return finalresults, results[1], results[2]
