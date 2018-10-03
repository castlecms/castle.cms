# -*- coding: utf-8 -*-
from lxml.html import fromstring
import unittest

from DateTime import DateTime
from castle.cms import archival
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.interfaces import IArchiveManager
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles


class TestArchival(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        man = archival.ArchiveManager()
        self.archive_manager = IArchiveManager(man)

    def test_get_archival_items(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        foobar = api.content.create(
            type='Document',
            id='foobar1',
            container=self.portal)
        api.content.transition(foobar, 'publish')
        foobar.setModificationDate(DateTime() - 10)
        foobar.reindexObject(idxs=['modified'])
        api.portal.set_registry_record(
            'castle.archival_number_of_days', 5)
        api.portal.set_registry_record(
            'castle.archival_types_to_archive', ['Document'])

        self.assertEqual(len(self.archive_manager.getContentToArchive()), 1)

    def test_get_archival_items_pays_attention_to_types(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        foobar = api.content.create(
            type='Document',
            id='foobar1',
            container=self.portal)
        api.content.transition(foobar, 'publish')
        foobar.setModificationDate(DateTime() - 10)
        foobar.reindexObject(idxs=['modified'])
        api.portal.set_registry_record(
            'castle.archival_number_of_days', 5)
        api.portal.set_registry_record(
            'castle.archival_types_to_archive', ['News Item'])

        self.assertEqual(len(self.archive_manager.getContentToArchive()), 0)

    def test_flash_resource_mover_gets_els(self):
        dom = fromstring('''<html>
<head>
<base href="https://www.foobar.com/foobar/"/><!--[if lt IE 7]></base><![endif]-->
</head><body>
<script type="text/javascript">
    AC_FL_RunContent('codebase','http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,28,0','width','920','height','670','src','foobar','quality','high','wmode','transparent','pluginspage','http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash','movie','foobar' );
    </script></body></html>''')  # noqa
        mover = archival.FlashScriptResourceMover(dom)
        els = mover.get_elements()
        self.assertEqual(len(els), 1)
        self.assertEqual(mover.get_url(els[0]),
                         'https://www.foobar.com/foobar/foobar.swf')
        mover.modify(els[0], "https://www.foobar.com/foobar/foobar.swf")
        self.assertTrue("https://www.foobar.com/foobar/foobar'" in els[0].text)

    def test_flash_resource_mover_gets_els_bad_markup(self):
        dom = fromstring('''<html>
<head>
<base href="https://www.foobar.com/foobar/avatars/avatars"/><!--[if lt IE 7]></base><![endif]-->
</head><body>
<script type="text/javascript">
    // &amp;amp;amp;amp;amp;amp;amp;amp;amp;amp;amp;lt;![CDATA[
    AC_FL_RunContent( 'codebase','http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,28,0','width','630','height','341','src','avatars_2','quality','high', 'wmode','transparent','pluginspage','http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash','movie','avatars_2?12' ); //end AC code
    // ]]&amp;amp;amp;amp;amp;amp;amp;amp;amp;amp;amp;gt;
    </script></body></html>''')  # noqa
        mover = archival.FlashScriptResourceMover(dom)
        els = mover.get_elements()
        self.assertEqual(len(els), 1)
        self.assertEqual(mover.get_url(els[0]),
                         'https://www.foobar.com/foobar/avatars/avatars_2.swf')
        mover.modify(els[0], "https://www.foobar.com/foobar/avatars/avatars_2.swf")
        self.assertTrue("https://www.foobar.com/foobar/avatars/avatars_2'" in els[0].text)

    def test_archive_replacement_text(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        storage = archival.Storage(self.portal)

        storage.replacements = {
            'foobar': 'barfoo'
        }

        self.assertEqual('<html><body><div>barfoo</div></body></html>',
                         storage.apply_replacements('<html><body><div>foobar</div>'
                                                    '</body></html>'))

    def test_archive_replacement_selector(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        storage = archival.Storage(self.portal)

        storage.replacements = {
            '.foobar': 'barfoo'
        }

        self.assertEqual('<html><body><div class="foobar">barfoo</div></body></html>',
                         storage.apply_replacements('<html><body><div class="foobar"></div>'
                                                    '</body></html>'))

    def test_archive_transformers(self):
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        storage = archival.Storage(self.portal)
        result = storage.transform_content(
            '<html><body><div class="foo">foo</div></body></html>',
            'http://foobar.com')

        self.assertTrue('>bar<' in result)
