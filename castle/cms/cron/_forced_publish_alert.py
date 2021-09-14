from AccessControl.SecurityManagement import newSecurityManager
from castle.cms import audit
from castle.cms import utils
from castle.cms.utils import ESConnectionFactoryFactory
from collective.elasticsearch.es import ElasticSearchCatalog
from DateTime import DateTime
from plone import api
from plone.app.uuid.utils import uuidToObject
from plone.registry.interfaces import IRegistry
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from tendo import singleton
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import setSite

import transaction


LAST_CHECKED_KEY = 'castle.forced-publish-last-checked'


EMAIL_BODY = """
<p>This content has been forced published:</p>
"""
EMAIL_BODY_ITEM = """
<li>
    <a href="{content_url}">{content_title}</a> - Published by {user_name}<br />
    <span class="font-size: 80%; color: #DDD">{comments}</span>
</li>"""


def check_site(site):
    # XXX will store when last check was so we always only look back
    # to previous check time
    setSite(site)
    catalog = api.portal.get_tool('portal_catalog')
    es = ElasticSearchCatalog(catalog)
    if not es.enabled:
        return

    index_name = audit.get_index_name()
    es = ESConnectionFactoryFactory()()

    sannotations = IAnnotations(site)
    last_checked = sannotations.get(LAST_CHECKED_KEY)
    if last_checked is None:
        last_checked = DateTime() - 30

    filters = [
        {'term': {'type': 'workflow'}},
        {'range': {'date': {'gt': last_checked.ISO8601()}}}
    ]

    if len(filters) > 1:
        qfilter = {'and': filters}
    else:
        qfilter = filters[0]
    query = {
        "query": {
            'filtered': {
                'filter': qfilter,
                'query': {'match_all': {}}
            }
        }
    }
    results = es.search(
        index=index_name,
        doc_type=audit.es_doc_type,
        body=query,
        sort='date:desc',
        size=1000)
    hits = results['hits']['hits']

    workflow = api.portal.get_tool('portal_workflow')
    forced = []
    checked = []
    for hit in hits:
        hit = hit['_source']
        if hit['object'] in checked:
            continue
        try:
            ob = uuidToObject(hit['object'])
            checked.append(hit['object'])
        except Exception:
            continue

        try:
            review_history = workflow.getInfoFor(ob, 'review_history')
            if not review_history:
                continue

            for r in reversed(review_history):
                if (not r['action'] or r['review_state'] != 'published' or
                        not r.get('comments', '').startswith('OVERRIDE:')):
                    continue
                if r['time'] < last_checked:
                    # just quit now, we're getting to older history that we don't care about
                    break
                forced.append({
                    'ob': ob,
                    'history_entry': r
                })
        except WorkflowException:
            continue

    if len(forced) > 0:
        # sent out email to admins
        site_url = site.absolute_url()
        registry = getUtility(IRegistry)
        public_url = registry.get('plone.public_url')
        if not public_url:
            public_url = site_url
        email_html = EMAIL_BODY + '<ul>'
        for item in forced:
            ob = item['ob']
            wf_entry = item['history_entry']
            try:
                user = api.user.get(wf_entry['actor'])
                user_name = user.getProperty('fullname') or user.getId()
            except Exception:
                user_name = wf_entry['actor']
            email_html += EMAIL_BODY_ITEM.format(
                content_url=ob.absolute_url().replace(site_url, public_url),
                content_title=ob.Title(),
                user_name=user_name,
                comments=wf_entry.get('comments', '')
            )
        email_html += '</ul>'
        email_subject = "Forced content publication update(Site: %s)" % (
            api.portal.get_registry_record('plone.site_title'))

        for user in api.user.get_users():
            user_roles = api.user.get_roles(user=user)
            email = user.getProperty('email')
            if (('Manager' not in user_roles and 'Site Administrator' not in user_roles) or
                    not email):
                continue

            utils.send_email(email, email_subject, html=email_html)

    site._p_jar.sync()
    sannotations[LAST_CHECKED_KEY] = DateTime()
    transaction.commit()


def run(app):
    singleton.SingleInstance('forcedpublishalert')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    for oid in app.objectIds():  # noqa
        obj = app[oid]  # noqa
        if IPloneSiteRoot.providedBy(obj):
            check_site(obj)


if __name__ == '__main__':
    run(app)  # noqa
