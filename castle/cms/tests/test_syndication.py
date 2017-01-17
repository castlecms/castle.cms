# -*- coding: utf-8 -*-
from castle.cms.testing import BaseTest
from Products.CMFPlone.browser.syndication.settings import FeedSettings

import json


class TestArchival(BaseTest):

    def test_json_feed_404_when_not_active(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = []
        resp = self.publish('/plone/feed.json')
        self.assertEqual(resp.status_code, 404)

    def test_json_feed_when_active(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = ['feed.json']
        resp = self.publish('/plone/feed.json')
        self.assertEqual(resp.status_code, 200)

    def test_json_feed_contents(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = ['feed.json']
        resp = self.publish('/plone/feed.json')
        result = json.loads(resp.body)
        self.assertEqual(result['title'], u'Plone site')
        self.assertEqual(
            len(result['items']), len(self.portal.portal_catalog()))
