from AccessControl.SecurityManagement import newSecurityManager
from DateTime import DateTime
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite

import logging
import transaction


logger = logging.getLogger('castle.cms')


def run_transitions(query_params):

    catalog = api.portal.get_tool('portal_catalog')
    content = catalog(**query_params)
    
    to_state = 'published' if query_params.get('effective') else 'private'
    for brain in content:
        obj = brain.getObject()
        api.content.transition(
            obj=obj, 
            to_state=to_state
        )
        obj.setModificationDate()
        obj.reindexObject(idxs=['modified'])
    transaction.commit()


def set_queries(site):
    setSite(site)

    # publish pending content with an effective date within 30 minutes of cron run
    start = DateTime(DateTime().timeTime() - (30 * 60))
    end = DateTime()
    publish_query = {
        'effective': {
            'query': (start, end),
            'range': 'min:max'
        },
        'review_state': ['pending', 'private']
    }
    run_transitions(publish_query)

    # retract published content with an expiration date older than cron run
    retract_query = {
        'expires': {
            'query': DateTime(),
            'range': 'max'
        },
        'review_state': 'published'
    }
    run_transitions(retract_query)


def run(app):
    singleton.SingleInstance('autopublish')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            try:
                set_queries(obj)
            except Exception:
                logger.error('Could not update content for %s' % oid, exc_info=True)


if __name__ == '__main__':
    run(app)  # noqa
