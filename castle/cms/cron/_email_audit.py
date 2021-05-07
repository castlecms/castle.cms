from castle.cms import audit
from castle.cms.utils import ESConnectionFactoryFactory
from AccessControl.SecurityManagement import newSecurityManager
from plone import api
from tendo import singleton
from Products.CMFCore.utils import getToolByName
from castle.cms.utils import send_email

import transaction

query = {
    "query": {
        "range": {
            "date": {
                "gte": "now-1d/d"
            }
        }
    }
}


def run_query():
    registry = getToolByName(app['Castle'], 'portal_registry')  # noqa: F821
    index_name = audit.get_index_name()
    es = ESConnectionFactoryFactory(registry)()

    results = es.search(
        index=index_name,
        filter_path=['hits.hits._source'],
        doc_type=audit.es_doc_type,
        body=query,
        sort='date:desc')

    return results


def generate_message(log):
    html = "<p>Here is today's Audit Log:</p><ul>"
    for entry in log:
        html += '<li>'
        for key, value in entry.items():
            html += '<div>{}: {}</div>'.format(key, value)

        html += '</li>'
    html += '</ul>'

    return html


def run(app):
    singleton.SingleInstance('emailaudit')

    user = app.acl_users.getUser('admin')
    newSecurityManager(None, user.__of__(app.acl_users))

    audit_log = run_query()['hits']['hits']
    audit_log = map(
        lambda hit: hit['_source'],
        audit_log
    )
    html = generate_message(audit_log)
    recipients = api.portal.get_registry_record("castle.daily_audit_log_recipients", default=[])
    transaction.begin()
    send_email(
        recipients, subject="Audit Log",
        html=html)
    transaction.commit()


if __name__ == '__main__':
    run(app)  # noqa: F821
