import argparse
import json
import os

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from DateTime import DateTime
from Persistence.mapping import PersistentMapping as PM1  # noqa
from Products.CMFCore.tests.base.security import (OmnipotentUser,
                                                  PermissiveSecurityPolicy)
from Testing.makerequest import makerequest
from zope.component.hooks import setSite

parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone')
parser.add_argument('--type', dest='type', default='Page')

args, _ = parser.parse_known_args()


def spoofRequest(app):
    """
    Make REQUEST variable to be available on the Zope application server.

    This allows acquisition to work properly
    """
    _policy = PermissiveSecurityPolicy()
    _oldpolicy = setSecurityPolicy(_policy)  # noqa
    newSecurityManager(None, OmnipotentUser().__of__(app.acl_users))
    return makerequest(app)

app = spoofRequest(app)  # noqa

user = app.acl_users.getUser('admin')  # noqa
newSecurityManager(None, user.__of__(app.acl_users))  # noqa
site = app[args.site_id]
setSite(site)

export_path = os.path.abspath('./archives.json')
catalog = site.portal_catalog
workflow = site.portal_workflow
ptool = site.plone_utils
site_path = '/'.join(site.getPhysicalPath())


def runExport(brains):
    items = []
    for brain in brains:
        items.append({
            'path': brain.getPath(),
            'uid': brain.UID
        })
        if len(items) % 100 == 0:
            print('exported %i' % len(items))
    fi = open(export_path, 'w')
    fi.write(json.dumps(items))
    fi.close()


runExport(catalog(
    portal_type=args.type,
    created={
        'query': (DateTime(1900, 1, 1), DateTime(2014, 1, 1)),
        'range': 'min:max'},
    allowedRolesAndUsers='Anonymous'))
