from castle.cms.browser.audit import AuditView as BaseAuditView


class AuditView(BaseAuditView):
    label = 'Audit Log'
    user = False
