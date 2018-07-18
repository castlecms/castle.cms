# -*- coding: utf-8 -*-
from castle.cms.testing import BaseTest
from plone.namedfile.file import NamedBlobImage
from plone.namedfile.tests.test_image import zptlogo
from Products.CMFPlone.browser.syndication.settings import FeedSettings

import json


class TestSyndication(BaseTest):

    def _get_image(self):
        return NamedBlobImage(zptlogo, contentType='image/jpeg',
                              filename=u'foobar.jpg')

    def test_json_feed_when_not_active(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = []
        resp = self.publish('/plone/feed.json')
        self.assertTrue(resp.status_code in [301, 302, 404])

    def test_json_feed_when_active(self):
        settings = FeedSettings(self.portal)
        settings.feed_types = ['feed.json']
        settings.enabled = True
        resp = self.publish('/plone/feed.json')
        self.assertEqual(resp.status_code, 200)

    def _test_json_feed_contents(self):
        # XXX fix tests(isolation issues)
        settings = FeedSettings(self.portal)
        settings.feed_types = ['feed.json']
        settings.enabled = True
        resp = self.publish('/plone/feed.json')
        result = json.loads(resp.body)
        self.assertEqual(result['title'], u'Plone site')
        self.assertEqual(
            len(result['items']), len(self.portal.portal_catalog()))

    def _test_image_url_with_json(self):
        # XXX fix test(isolation issues)
        settings = FeedSettings(self.portal)
        settings.enabled = True
        settings.feed_types = ['feed.json']
        page = self.portal['front-page']
        page.image = self._get_image()

        resp = self.publish('/plone/feed.json')
        result = json.loads(resp.body)
        base_url = page.absolute_url()
        self.assertEqual(
            result['items'][0]['image_url'],
            '{}/@@images/image'.format(base_url))
        self.assertEqual(
            result['items'][0]['file_url'],
            '{}/@@download/image/{}'.format(base_url, page.image.filename))
