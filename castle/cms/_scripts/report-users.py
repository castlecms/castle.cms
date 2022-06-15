"""
The data submitted to a GELF endpoint logger for this is using a schema that
looks something like this:

class UserAccess(BaseModel):
    appname: str
    site: str
    logid: str
    reportid: str
    username: str
    group: str
    permissions: list[str]

In this case, Plone (by way of Zope and AccessControl) assigns *permissions*
to *roles*, and *roles* to *users* in a 3-layer approach.

Therefore, in the above model, the following are mapped to an individual record:

    - username == user.getUserName()
    - group == a single 
"""
from argparse import ArgumentParser
import csv
from datetime import datetime
import logging
import os
import sys
import uuid

from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite

from castle.cms.gelf import GELFHandler



logger = logging.getLogger("Plone")


APP_NAME = "castle.cms"
LOG_ID = "UserGroupMatrix"
gelflogger = logging.getLogger(LOG_ID)
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
        "appname": APP_NAME,
        "site": site.id,
        "logid": LOG_ID,
        "reportid": uuid.uuid4(),
    }

    users = api.user.get_users()
    for user in users:
        extras["username"] = user.getUserName()

        # for each role
        # - for each permission
        # -- is the permission selected for the role?
        # --- add permission to role's permission list

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
            msg = "{appname} {site} {logid} {reportid} {username} {rolename} {permissions}".format(
                appname=extras["appname"],
                site=extras["site"]
                logid=extras["logid"],
                reportid=extras["reportid"],
                username=extras["username"],
                rolename=rp,
                permissions=",".join(roleperms[rp]))
            extras["group"] = rp
            extras["permissions"] = roleperms[rp]
            gelflogger.info(msg, extras=extras)


def run(app):
    singleton.SingleInstance('importauditlog')

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


if __name__ == '__main__':
    run(app)  # noqa: F821
