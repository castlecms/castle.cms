# -*- coding: utf-8 -*-
# for compat with python3, specifically the urllib.parse includes
# noqa because these need to precede other imports
from future.standard_library import install_aliases
install_aliases()  # noqa

from lxml.html import fromstring
import unittest
from urllib.parse import unquote_plus

import boto3
import botocore
from DateTime import DateTime
from castle.cms import archival
from castle.cms.files import aws
from castle.cms.testing import CASTLE_PLONE_INTEGRATION_TESTING
from castle.cms.interfaces import IArchiveManager
from moto import mock_s3
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles


class TestArchiveManager(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        man = archival.ArchiveManager()
        self.archive_manager = IArchiveManager(man)

    def test_get_archival_items(self):
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


class TestFlashScriptResourceMover(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']

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


class TestStorage(unittest.TestCase):
    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.test_access_key = u'AKIAIOSFODNN7EXAMPLE'
        self.test_secret_key = u'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        self.test_bucket_name = u'castletest'
        self.test_bucket_endpoint = u'https://s3.amazonaws.com'
        self.test_base_url = u'https://localhost.localdomain/'  # used for test swap
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        api.portal.set_registry_record('castle.aws_s3_key', self.test_access_key)
        api.portal.set_registry_record('castle.aws_s3_secret', self.test_secret_key)
        api.portal.set_registry_record('castle.aws_s3_bucket_name', self.test_bucket_name)
        api.portal.set_registry_record('castle.aws_s3_host_endpoint', self.test_bucket_endpoint)
        api.portal.set_registry_record('castle.aws_s3_base_url', self.test_base_url)

    @mock_s3
    def test_move_to_aws(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3', endpoint_url=self.test_bucket_endpoint)
        s3conn.create_bucket(Bucket='castletest')
        s3, bucket = aws.get_bucket("castletest")

        storage = archival.Storage(self.portal)
        content = "this is a test"
        content_path = "a/test/path/for/this/test.html"
        content_type = "text/html; charset=utf-8"

        # the key should not be there before we run through this
        self.assertRaises(botocore.exceptions.ClientError, lambda: bucket.Object(content_path).load())

        storage.move_to_aws(content, content_path, content_type)

        try:
            bucket.Object(archival.CONTENT_KEY_PREFIX + content_path).load()
        except botocore.exceptions.ClientError:
            self.fail("object does not exist after move")

    @mock_s3
    def test_move_resource(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3', endpoint_url=self.test_bucket_endpoint)
        s3conn.create_bucket(Bucket='castletest')
        s3, bucket = aws.get_bucket("castletest")

        storage = archival.Storage(self.portal)

        testcontent = 'this is some content'
        moveresource = api.content.create(
            type='Document',
            id='moveresource',
            container=self.portal)
        moveresource.content = testcontent
        api.content.transition(moveresource, 'publish')
        vpath = "/moveresource"
        url = self.portal.absolute_url() + vpath

        new_url = storage.move_resource(url, use_vhm=False)

        self.assertIsNotNone(new_url)

        try:
            # trim off, e.g., 'https://s3.amazonaws.com/bucketname'
            # and then convert the path back from the url escaped version
            droppart = "{}/{}/".format(self.test_bucket_endpoint, self.test_bucket_name)
            content_path = unquote_plus(new_url[len(droppart):])
            bucket.Object(content_path).load()
        except botocore.exceptions.ClientError:
            self.fail("object does not exist after move")

        # move by url of content again
        new_url2 = storage.move_resource(url, use_vhm=False)
        self.assertEqual(new_url, new_url2)

        # test for existence of content in aws still
        try:
            # trim off 'https://s3.amazonaws.com/castletest/'
            # and then convert the path back from the url escaped version
            droppart = "{}/{}/".format(self.test_bucket_endpoint, self.test_bucket_name)
            content_path = unquote_plus(new_url[len(droppart):])
            bucket.Object(content_path).load()
        except botocore.exceptions.ClientError:
            self.fail("object does not exist after move")

    def test_archive_replacement_text(self):
        storage = archival.Storage(self.portal)

        storage.replacements = {
            'foobar': 'barfoo'
        }

        self.assertEqual('<html><body><div>barfoo</div></body></html>',
                         storage.apply_replacements('<html><body><div>foobar</div>'
                                                    '</body></html>'))

    def test_archive_replacement_selector(self):
        storage = archival.Storage(self.portal)

        storage.replacements = {
            '.foobar': 'barfoo'
        }

        self.assertEqual('<html><body><div class="foobar">barfoo</div></body></html>',
                         storage.apply_replacements('<html><body><div class="foobar"></div>'
                                                    '</body></html>'))

    def test_archive_transformers(self):
        storage = archival.Storage(self.portal)
        result = storage.transform_content(
            '<html><body><div class="foo">foo</div></body></html>',
            'http://foobar.com')

        self.assertTrue('>bar<' in result)
