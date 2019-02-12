from AccessControl.SecurityManagement import newSecurityManager
from castle.cms.linkreporter import Reporter
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton


def run_link_report(site):
    reporter = Reporter(site)
    if not reporter.valid:
        return
    try:
        reporter()
    except KeyboardInterrupt:
        reporter.join()


def run(app):
    singleton.SingleInstance('linkreport')

    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))

    for oid in app.objectIds():
        obj = app[oid]
        if IPloneSiteRoot.providedBy(obj):
            run_link_report(obj)


if __name__ == '__main__':
    run(app)  # noqa
