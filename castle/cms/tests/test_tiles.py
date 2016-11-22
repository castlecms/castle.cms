# -*- coding: utf-8 -*-
import unittest
from plone import api
from castle.cms.tests.utils import render_tile, get_tile
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from castle.cms.tiles.querylisting import QueryListingTile


class TestTiles(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING
    prefix = 'castle.cms.'

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_subscribe_render(self):

        name = self.prefix + 'subscription'
        data = {}

        page = render_tile(self.request, self.portal, name, data)

        # Not really much to test here?
        # Just make sure the form renders
        self.assertTrue('form.buttons.subscribe' in page)

    def test_facebook_render(self):

        name = self.prefix + 'facebookPage'
        data = {
            'href': u'https://www.facebook.com/plonecms/?fref=ts',
            'timeline': 'timeline'
        }
        page = render_tile(self.request, self.portal, name, data)
        self.assertTrue('data-tabs="timeline"' in page)
        self.assertTrue('data-href="https://www.facebook.com/plonecms"' in page)

    def test_sharebutton_render(self):

        name = self.prefix + 'sharing'
        data = {
            'buttons': ['twitter', 'facebook']
        }

        page = render_tile(self.request, self.portal, name, data)

        self.assertTrue('Share on Facebook' in page)
        self.assertTrue('Share on Twitter' in page)

    def test_pinterest_render(self):
        name = self.prefix + 'pin'
        data = {
            'url': u'https://www.pinterest.com/pin/546413367268498761/'
        }

        page = render_tile(self.request, self.portal, name, data)
        self.assertTrue('data-pin-do="embedPin"' in page)
        self.assertTrue('href="https://www.pinterest.com/pin/546413367268498761/"' in page)

    def test_timeline_render(self):

        name = self.prefix + 'twitterTimeline'
        data = {
            'screenName': u'plone',
            'theme': u'dark'
        }
        page = render_tile(self.request, self.portal, name, data)
        # Twitter WidgetID set by default
        self.assertTrue('684100313582833665' in page)
        # Checking for other simple configurations
        self.assertTrue('data-pat-timeline' in page)
        self.assertTrue('plone' in page)

    def test_tweet_render(self):

        name = self.prefix + 'tweet'
        data = {
            'url': u'https://twitter.com/xkcdComic/status/678810713033277440',
            'cards': 'hidden'
        }

        page = render_tile(self.request, self.portal, name, data)
        # Pretty much just assuring it renders correctly.
        # Not much else to do here
        self.assertTrue('678810713033277440' in page)
        self.assertTrue('data-pat-tweet' in page)
        self.assertTrue('hidden' in page)

    def test_video_render(self):
        name = self.prefix + 'videotile'
        data = {
            'youtube_url': u'https://www.youtube.com/watch?v=wZZ7oFKsKzY'
        }

        page = render_tile(self.request, self.portal, name, data)
        self.assertTrue('https://www.youtube-nocookie.com/embed/wZZ7oFKsKzY' in page)
        self.assertTrue('iframe' in page)

    def test_map_render(self):
        name = self.prefix + 'maptile'
        data = {
            'center': '{"formatted":"Oshkosh, WI, USA","lat":44.0247062,"lng":-88.54261359999998}'
        }

        page = render_tile(self.request, self.portal, name, data)
        self.assertTrue('class="map-container"' in page)
        self.assertTrue('Oshkosh, WI' in page)

    def test_calendar_render(self):
        name = self.prefix + 'calendar'
        data = {}

        # create an event for today to make sure the calendar reflects
        # current events
        api.content.create(type='Event', id='event1', container=self.portal)

        page = render_tile(self.request, self.portal, name, data)
        self.assertTrue('data-pat-fullcalendar=' in page)
        # make sure there's a link to the event in the calendar
        self.assertTrue('event1' in page)

    def test_embed_render(self):
        embedCode = '<iframe width="560" height="315" src="https://www.youtube.com/embed/JbpgM-JTang" frameborder="0" allowfullscreen></iframe>'  # noqa

        name = self.prefix + 'embedtile'
        data = {
            'code': embedCode
        }

        page = render_tile(self.request, self.portal, name, data)

        # Embed tile just spits the embed code back out onto the page.
        self.assertTrue(embedCode in page)

    def test_querylisting_results(self):
        api.content.create(type='Document', id='page1', container=self.portal,
                           subject=('foobar',))
        api.content.create(type='Document', id='page2', container=self.portal,
                           subject=('foobar',))
        api.content.create(type='Document', id='page3', container=self.portal,
                           subject=('foobar', 'foobar2'))
        api.content.create(type='Document', id='page4', container=self.portal,
                           subject=('foobar', 'foobar2'))
        data = {
            'query': [{
                'i': 'Subject',
                'o': 'plone.app.querystring.operation.list.contains',
                'v': 'foobar2'
            }],
            'available_tags': ('foobar2',)
        }
        tile = get_tile(self.request, self.portal, 'castle.cms.querylisting', data)
        self.assertEqual(tile.results()['total'], 2)

        self.request.form.update({
            'Subject': 'foobar'
        })
        tile = get_tile(self.request, self.portal, 'castle.cms.querylisting', data)
        self.assertEqual(tile.results()['total'], 2)
