# -*- coding: utf-8 -*-
import json
import unittest

import mock
from castle.cms.browser.content.analytics import AnalyticsView
from castle.cms.social import COUNT_ANNOTATION_KEY
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from zope.annotation.interfaces import IAnnotations


class TestAnalytics(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        if 'front-page' not in self.portal:
            api.content.create(type='Document', id='front-page',
                               container=self.portal)

            self.portal.setDefaultPage('front-page')
        self.page = self.portal['front-page']

        annotations = IAnnotations(self.page)
        annotations[COUNT_ANNOTATION_KEY] = {
            'twitter': 5,
            'facebook': 5,
            'linkedin': 5
        }

    def test_get_stats(self):
        view = AnalyticsView(self.page, self.request)
        self.assertEquals(json.loads(view())['data']['twitter'], 5)

    @mock.patch('castle.cms.cache.get')
    @mock.patch('castle.cms.cache.set')
    @mock.patch('castle.cms.services.google.analytics.get_ga_profile')
    @mock.patch('castle.cms.services.google.analytics.get_ga_service')
    def test_ga_api_call(self, get_ga_service, get_ga_profile,
                         cache_set, cache_get):
        cache_get.side_effect = KeyError()
        view = AnalyticsView(self.page, self.request)
        self.request.form.update({
            'params': json.dumps({'foo': 'bar'})
        })
        view.ga_api_call(['/'])
        self.assertEquals(get_ga_service.call_count, 1)
        self.assertEquals(get_ga_profile.call_count, 1)

    @mock.patch('castle.cms.cache.get')
    @mock.patch('castle.cms.cache.set')
    @mock.patch('castle.cms.services.google.analytics.get_ga_profile')
    def test_get_ga_profile(self, get_ga_profile, cache_set, cache_get):
        cache_get.side_effect = KeyError()
        view = AnalyticsView(self.page, self.request)
        service_mock = mock.MagicMock()
        view.get_ga_profile(service_mock)
        self.assertEquals(cache_set.call_count, 1)
        self.assertEquals(cache_get.call_count, 1)
        self.assertEquals(get_ga_profile.call_count, 1)

    def test_get_paths(self):
        view = AnalyticsView(self.page, self.request)
        paths = view.get_paths()

        self.assertTrue('/' in paths)
        self.assertTrue('/front-page' in paths)
