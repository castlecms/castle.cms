# -*- coding: utf-8 -*-
from castle.cms._scripts.cleanup_archive import is_s3_url
from castle.cms import archival
from castle.cms.testing import CASTLE_PLONE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from moto import mock_s3

import unittest
from urlparse import urlparse


class TestCleanupArchive(unittest.TestCase):
    layer = CASTLE_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.test_access_key = u'AKIAIOSFODNN7EXAMPLE'
        self.test_secret_key = u'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        self.test_bucket_name = u'castletest'
        # possibly useful to set under some condition...
        self.test_bucket_endpoint = u'https://s3.amazonaws.com/castletest'
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

    def tearDown(self):
        pass

    @mock_s3
    def test_is_s3_url(self):
        site = api.portal.get()
        storage = archival.Storage(site)
        parsed_endpoint = urlparse(storage.s3_conn.meta.client.meta.endpoint_url)

        urlstr = "http://localhost:9000/{}/{}".format(self.test_bucket_name, self.test_access_key)
        self.assertFalse(is_s3_url(urlstr, parsed_endpoint))

        urlstr = "https://s3.amazonaws.com/{}/{}".format(self.test_bucket_name, self.test_access_key)
        self.assertTrue(is_s3_url(urlstr, parsed_endpoint))
