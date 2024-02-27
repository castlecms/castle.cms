from AccessControl.SecurityManagement import newSecurityManager
from DateTime import DateTime
from plone import api
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.component.hooks import setSite

import logging
import transaction


logger = logging.getLogger('castle.cms')



def set_queries(site):
    setSite(site)

    # publish pending content with an effective date within 30 minutes of cron run
    start = DateTime(DateTime().timeTime() - (30 * 60))
    end = DateTime()
    publish_query = {
        'modified': {
            'query': (start, end),
            'range': 'min:max'
        },
    }

    retract_query = {
        'expires': {
            'query': DateTime(),
            'range': 'max'
        },
        'review_state': 'published'
    }
    catalog = api.portal.get_tool('portal_catalog')
    content = catalog(**retract_query)
    
    print('=== content ===')
    for brain in content:
        obj = brain.getObject()
        print(obj)
        print(obj.modified())


    # if email:
    #     name = user.getProperty('fullname') or user.getId()
    #     try:
    #         utils.send_email(
    #             recipients=email,
    #             subject="Paste Operation Failed(Site: %s)" % (
    #                 api.portal.get_registry_record('plone.site_title')),
    #             html="""
    #                 <p>Hi %s,</p>

    #                 <p>The site has failed to paste your items into the /%s folder.</p>

    #                 <p>Please contact your administrator.</p>""" % (
    #                                     name, where.lstrip('/')))
    #     except Exception:
    #         logger.warn('Could not send status email ', exc_info=True)


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
