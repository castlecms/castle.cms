from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite
import os
import shutil
import tempfile

import logging


logger = logging.getLogger('castle.cms')


def clean_dir(site):
    setSite(site)

    site = api.portal.get()
    prefix = "{}-uploads".format(site.getId())
    tmp_dir = tempfile.gettempdir()

    for item in os.listdir(tmp_dir):
        if prefix in item:
            path = "{}/{}".format(tmp_dir, item)
            shutil.rmtree(path)


def run(app):
    singleton.SingleInstance('cleantmpdir')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            try:
                clean_dir(obj)
            except Exception:
                logger.error('Could not clean /tmp directory for %s' % oid, exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa