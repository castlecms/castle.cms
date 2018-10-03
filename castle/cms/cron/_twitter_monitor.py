from AccessControl.SecurityManagement import newSecurityManager
from BTrees.OOBTree import OOBTree
from castle.cms.services import twitter
from castle.cms.social import COUNT_ANNOTATION_KEY
from castle.cms.utils import index_in_es
from castle.cms.utils import retriable
from castle.cms.services.twitter import get_auth
from datetime import datetime
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.log import logger
from tendo import singleton
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.component.hooks import setSite

import json
import sys
import time
import transaction


def record_tweet_stats(site, ob, tweet):
    """
    Keep daily totals...
    Total score includes complete impression(so favorites)
    """

    site._p_jar.sync()
    annotations = IAnnotations(ob)
    social_data = annotations.get(COUNT_ANNOTATION_KEY, OOBTree())
    stats = social_data.get('twitter', {
        'total': 0
    })

    score = 1 + tweet['favorite_count']

    now = datetime.utcnow()
    if now.year not in stats:
        year = stats[now.year] = {}
    else:
        year = stats[now.year]
    if now.month not in year:
        month = year[now.month] = {}
    else:
        month = year[now.month]
    if now.day not in month:
        month[now.day] = score
    else:
        month[now.day] += score

    stats['total'] += score
    social_data['twitter'] = stats
    annotations[COUNT_ANNOTATION_KEY] = social_data
    transaction.commit()


@retriable(sync=True)
def parse_line(site, public_url, line):
    tweet = json.loads(line)
    modified = False
    for url in tweet['entities']['urls']:
        if url['expanded_url'].startswith(public_url):
            path = url['expanded_url'].replace(
                public_url, '').split('?')[0].strip('/')
            ob = None
            if path in ('', '/'):
                try:
                    ob = site[site.default_page]
                except Exception:
                    pass
            else:
                ob = site.restrictedTraverse(path, None)
            if ob is None:
                redirector = getUtility(IRedirectionStorage)
                obj_path = redirector.get(path, default=None)
                if obj_path:
                    ob = site.restrictedTraverse(obj_path, None)
            if ob:
                modified = True
                record_tweet_stats(site, ob, tweet)
    if modified:
        transaction.commit()
        index_in_es()


class StreamListener(twitter.StreamListener):
    def __init__(self, site, public_url):
        self.site = site
        self.public_url = public_url

    def on_data(self, raw_data):
        try:
            parse_line(self.site, self.public_url, raw_data)
        except Exception:
            logger.warn('error parsing tweet', exc_info=True)


def attempt_twitter_on_site(site):
    setSite(site)

    registry = getUtility(IRegistry)
    public_url = registry.get('plone.public_url', None)
    if not public_url:
        return

    auth = get_auth()

    if auth is None:
        return

    # normlize url...
    original_url = public_url = public_url.replace(
        'http://', '').replace('https://', '').strip('/')
    if public_url.count('.') > 1:
        _, _, public_url = public_url.partition('.')

    stream = twitter.Stream(auth, StreamListener(site, original_url))
    stream.filter(track=[' '.join(public_url.split('.'))])


def run(app):
    singleton.SingleInstance('twittermonitor')

    user = app.acl_users.getUser('admin')  # noqa
    newSecurityManager(None, user.__of__(app.acl_users))  # noqa

    while True:
        try:
            if 'site-id' in sys.argv:
                siteid = sys.argv['site-id']
                attempt_twitter_on_site(app[siteid])  # noqa
            else:
                for oid in app.objectIds():  # noqa
                    obj = app[oid]  # noqa
                    if IPloneSiteRoot.providedBy(obj):
                        attempt_twitter_on_site(obj)
        except KeyError:
            pass
        logger.info('Could not find valid site to monitor')
        time.sleep(10 * 60)


if __name__ == '__main__':
    run(app)  # noqa
