from AccessControl.SecurityManagement import newSecurityManager
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite
from plone import api

import logging
import transaction
import time


logger = logging.getLogger('castle.cms')


DRAFT_DURATION = 60 * 60 * 1  # 1 hour


def clean(site):
    setSite(site)
    pdrafts = api.portal.get_tool('portal_drafts')
    for userid in pdrafts.drafts.keys():
        draft_groups = pdrafts.drafts[userid]
        for uid in draft_groups.keys():
            drafts = draft_groups[uid]
            for draft_name in drafts.keys():
                draft = drafts[draft_name]
                if (time.time() - draft._p_mtime) >= DRAFT_DURATION:
                    logger.info('cleaning draft {}'.format(uid))
                    pdrafts.discardDraft(draft)
    transaction.commit()


def run(app):
    singleton.SingleInstance('cleanusers')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            try:
                clean(obj)
            except Exception:
                logger.error('Could not clean users %s' % oid, exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa
