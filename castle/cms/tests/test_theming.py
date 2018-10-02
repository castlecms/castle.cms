# -*- coding: utf-8 -*-
from castle.cms import theming
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from plone.registry import field as registry_field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from repoze.xmliter.utils import getHTMLSerializer
from zope.component import getUtility

import unittest


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
        self.assertTrue('<div>foobar</div>' in ''.join(result))
        self.assertTrue('data-pat-structure' in ''.join(result))

    def test_use_default_layout_in_registry(self):
        transform = theming.getTransform(self.portal, self.request)
        layout_name = transform.get_layout_name(self.portal)
        self.assertEqual(layout_name, 'index.html')
        registry = getUtility(IRegistry)
        field = registry_field.TextLine(title=u'Default layout',
                                        required=False)
        new_record = Record(field)
        registry.records['castle.cms.default_layout'] = new_record
        registry['castle.cms.default_layout'] = u'foobar.html'
        layout_name = transform.get_layout_name(self.portal)
        self.assertEqual(layout_name, 'foobar.html')

    def test_apply_does_not_transform_inner_content(self):
        transform = theming.getTransform(self.portal, self.request)
        self.request.environ['X-CASTLE-LAYOUT'] = MINIMAL_LAYOUT
        result = ''.join(transform(self.request, getHTMLSerializer(['''
<div id="content">
<a href="foo/bar" />
</div>''']), context=self.portal))
        self.assertTrue('++theme++castle.theme/foo/bar' not in result)
        self.assertTrue('http://nohost/plone/foo/bar' in result)
