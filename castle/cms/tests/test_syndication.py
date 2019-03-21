# -*- coding: utf-8 -*-
import json

from castle.cms.testing import BaseTest
from plone.namedfile.file import NamedBlobImage
from plone.namedfile.tests.test_image import zptlogo
from Products.CMFPlone.browser.syndication.settings import FeedSettings


class TestSyndication(BaseTest):

    def _get_image(self):
        return NamedBlobImage(zptlogo, contentType='image/jpeg',
                              filename=u'foobar.jpg')

    def test_json_feed_when_not_active(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = []
        resp = self.publish('/plone/feed.json')
        self.assertTrue(resp.status in [301, 302, 404])

    def test_json_feed_when_active(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = ['feed.json']
        settings.enabled = True
        resp = self.publish('/plone/feed.json')
        self.assertEqual(resp.status, 200)

    def test_json_feed_contents(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = ['feed.json']
        settings.enabled = True
        resp = self.publish('/plone/feed.json')
        result = json.loads(resp.body)
        self.assertEqual(result['title'], u'Plone site')
        self.assertEqual(
            len(result['items']), len(self.portal.portal_catalog()))
