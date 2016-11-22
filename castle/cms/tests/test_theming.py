# -*- coding: utf-8 -*-
import unittest

from castle.cms import trash
from castle.cms.interfaces import ITrashed
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from castle.cms import theming


MINIMAL_LAYOUT = """<!doctype html>
<html class="no-js" lang="en-us" data-gridsystem="bs3">
  <head>
    <meta charset="utf-8" />

    <link data-tile="${portal_url}/@@castle.cms.metadata"/>

    <link data-tile="${portal_url}/@@plone.app.standardtiles.stylesheets"/>

    <meta name="generator" content="Castle - https://www.wildcardcorp.com"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  </head>
  <body id="visual-portal-wrapper">
    <div data-tile="${context_url}/@@plone.app.standardtiles.toolbar" />

      <!-- Main Content -->
      <div class="row" id="main-content-container">
        <div id="main-content">
            ${structure: content.main}
        </div>
      </div>

      <link data-tile="${portal_url}/@@plone.app.standardtiles.javascripts"/>
  </body>
</html>
"""


MINIMAL_RESULT = '''<!doctype html>
<html>
  <head>
  </head>
  <body id="visual-portal-wrapper">
    <div>foobar</div>
  </body>
</html>'''


class TestTheming(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def test_get_layout(self):
        transform = theming.getTransform(self.portal, self.request)
        layout = transform.get_layout(self.portal)
        self.assertEqual(layout.name, 'index.html')

    def test_get_layout_from_environ(self):
        transform = theming.getTransform(self.portal, self.request)
        self.request.environ['X-CASTLE-LAYOUT'] = MINIMAL_LAYOUT
        layout = transform.get_layout(self.portal, request=self.request)
        self.assertEqual(layout.name, 'environ')

    def test_apply(self):
        transform = theming.getTransform(self.portal, self.request)
        result = transform(self.request, MINIMAL_RESULT, context=self.portal)
        self.assertTrue('<div>foobar</div>' in result)
        self.assertTrue('data-pat-structure' in result)
