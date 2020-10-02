from Products.CMFPlone.resources import add_resource_on_request
from castle.cms.browser.audit import AuditView as BaseAuditView


class AuditView(BaseAuditView):
    def __call__(self):
        # utility function to add resource to rendered page
        add_resource_on_request(self.request, 'castle-components-audit')
        return super(AuditView, self).__call__()

    label = 'Audit Log'
    user = False
