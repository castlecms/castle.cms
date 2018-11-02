from castle.cms import subscribe
from castle.cms import utils
from castle.cms.browser.utils import Utils
from collective.celery import task
from plone import api
from urllib import urlencode
from zope.globalrequest import getRequest


@task.as_admin()
def send_email(*args, **kwargs):
    utils.send_email(*args, **kwargs)


@task.as_admin()
def send_email_to_subscribers(subject, html, categories=None, sender=None):
    _utils = Utils(api.portal.get(), getRequest())
    public_url = _utils.get_public_url()

    check_categories = (categories is not None and len(categories) != 0)

    for subscriber in subscribe.all():
        if check_categories:
            # If there's no chosen categories, they recieve everything
            if ('categories' in subscriber and
                    len(subscriber['categories']) > 0):
                # make sure that this message falls under one of
                # their categories
                if len(categories.intersection(subscriber['categories'])) == 0:
                    continue

        query = urlencode({
            'email': subscriber.get('email'),
            'code': subscriber.get('code')
            })

        unsubscribe_url = '%s/@@unsubscribe?%s' % (
            public_url.rstrip('/'),
            query)

        change_url = '%s/@@changesubscription?%s' % (
            public_url.rstrip('/'),
            query)

        unsubscribe_url = unsubscribe_url.encode('utf8')
        change_url = change_url.encode('utf8')

        html = html.replace('{{unsubscribe_url}}', unsubscribe_url)
        html = html.replace('{{change_url}}', change_url)

        utils.send_email([subscriber.get('email')], subject, html, sender=sender)
