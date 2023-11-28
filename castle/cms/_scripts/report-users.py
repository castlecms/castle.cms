"""
The data submitted to a GELF endpoint logger for this is using a schema that
looks something like this:

class UserAccess(BaseModel):
    schema_version: str
    schema_type: str
    app_name: str
    site: str
    report_id: str
    username: str
    group: str
    permissions: list[str]

In this case, Plone (by way of Zope and AccessControl) assigns *permissions*
to *roles*, and *roles* to *users* in a 3-layer approach.

Therefore, in the above model, the following are mapped to an individual record:

    - username == user.getUserName()
    - group == a single role
    - permissions == all permissions associated with the Role that are active for the user

    - schema_version == SCHEMA_VERSION variable
    - schema_type == SCHEMA_TYPE variable
    - app_name == APP_NAME variable
    - site == app[site].id value
    - report_id == UUID4 unique per-site and per-execution of this script
"""
from argparse import ArgumentParser
import logging
import os
import uuid

from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite

from castle.cms.gelf import GELFHandler


logger = logging.getLogger("Plone")


SCHEMA_VERSION = "1"
SCHEMA_TYPE = "UserGroupMatrix"
APP_NAME = "castle.cms"
gelflogger = logging.getLogger(SCHEMA_TYPE)
gelfhandler = GELFHandler()
gelfformatter = logging.Formatter("%(asctime)s %(name)s [%(levelname)s] %(message)s")
gelfhandler.setFormatter(gelfformatter)
gelflogger.addHandler(gelfhandler)


def get_args():
    parser = ArgumentParser(
        description='Get a report of permissions by role and user')
    parser.add_argument('--site-id', dest='site_id', default='Castle')
    args, _ = parser.parse_known_args()
    return args


def report_on_users(site):
    extras = {
        "schema_version": SCHEMA_VERSION,
        "schema_type": SCHEMA_TYPE,
        "app_name": APP_NAME,
        "site": site.id,
        "report_id": uuid.uuid4(),
    }

    users = api.user.get_users()
    for user in users:
        extras["username"] = user.getUserName()

        perms = api.user.get_permissions(user=user)
        roles = api.user.get_roles(user=user)
        roleperms = {}

        # roles is a list of names of roles the user has
        # perms is a dict of permname:bool of what the user has
        # go through each role the user has, then collect the permissions associated with that
        #   specific role by iterating through roles related to each permission the user has.
        #
        #   I know what you're thinking, but yes, this is how it needs to be done (for now).
        #   the upstream packages don't have a convenient way to just get a list of
        #   permissions associated with a given role. They either give all permissions or roles
        #   associated with a user, or get all roles associated with a permission.
        #   Useful in most contexts outside of generating a report like this.
        for role in roles:
            roleperms[role] = []
            for perm in perms.keys():
                if perms[perm]:
                    roleperms[role].append(perm)

        for rp in roleperms.keys():
            msg = "{schemaversion} {schematype} {appname} {site} {reportid} {username} {rolename} {permissions}".format(  # noqa: E501
                schemaversion=extras["schema_version"],
                schematype=extras["schema_type"],
                appname=extras["app_name"],
                site=extras["site"],
                reportid=extras["report_id"],
                username=extras["username"],
                rolename=rp,
                permissions=",".join(roleperms[rp]))
            extras["group"] = rp
            extras["permissions"] = roleperms[rp]
            gelflogger.info(msg, extras=extras)


def run(app):
    singleton.SingleInstance('reportusers')

    args = get_args()

    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))

    if args.site_id.strip().lower() == "_all_":
        for oid in app.objectIds():
            obj = app[oid]
            if IPloneSiteRoot.providedBy(obj):
                setSite(obj)
                report_on_users(obj)
    else:
        site = app[args.site_id]
        setSite(site)
        report_on_users(site)


def setup_and_run():
    conf_path = os.getenv("ZOPE_CONF_PATH", "parts/instance/zope.conf")
    if conf_path is None or not os.path.exists(conf_path):
        raise Exception('Could not find zope.conf at {}'.format(conf_path))

    from Zope2 import configure
    configure(conf_path)
    import Zope2
    app = Zope2.app()
    from Testing.ZopeTestCase.utils import makerequest
    app = makerequest(app)
    app.REQUEST['PARENTS'] = [app]
    from zope.globalrequest import setRequest
    setRequest(app.REQUEST)
    from AccessControl.SpecialUsers import system as user
    from AccessControl.SecurityManagement import newSecurityManager
    newSecurityManager(None, user)

    run(app)


if __name__ == '__main__':
    run(app)  # noqa: F821
