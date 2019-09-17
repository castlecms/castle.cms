# -*- coding: utf-8 -*-
from castle.cms.browser import content
import castle.cms.files.aws as aws
from castle.cms.files.duplicates import DuplicateDetector
from castle.cms.testing import (
    CASTLE_PLONE_INTEGRATION_TESTING,
    CASTLE_PLONE_FUNCTIONAL_TESTING,
)
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IUUID

from io import BytesIO
import json
import os
import unittest


class TestDuplicateDetector(unittest.TestCase):

    layer = CASTLE_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))

    def test_register(self):
        dd = DuplicateDetector()
        hash_ = 'foobar'
        doc = api.content.create(
            type='Document',
            id='folder',
            container=self.portal)
        dd.register(doc, hash_)

        self.assertEqual(IUUID(dd.get_object(hash_)), IUUID(doc))


AWS_ENABLED = False
if "ENABLE_AWS_TEST_WITH_MINIO" in os.environ:
    AWS_ENABLED = True


if AWS_ENABLED:
    class TestAWS(unittest.TestCase):
        layer = CASTLE_PLONE_FUNCTIONAL_TESTING

        def setUp(self):
            minio_access_key = u'AKIAIOSFODNN7EXAMPLE'
            minio_secret_key = u'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
            minio_bucket_name = u'castletest'
            minio_bucket_endpoint = u'http://localhost:9000/'
            minio_base_url = u'https://localhost.localdomain/'  # used for test swap
            #os.system('docker run -d --name=minio_castle_test -p 9000:9000 -it -e "MINIO_ACCESS_KEY={0}" -e "MINIO_SECRET_KEY={1}" minio/minio server /data'.format(
            #    minio_access_key,
            #    minio_secret_key))
            self.portal = self.layer['portal']
            self.request = self.layer['request']
            login(self.portal, TEST_USER_NAME)
            setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
            api.portal.set_registry_record('castle.aws_s3_key', minio_access_key)
            api.portal.set_registry_record('castle.aws_s3_secret', minio_secret_key)
            api.portal.set_registry_record('castle.aws_s3_bucket_name', minio_bucket_name)
            api.portal.set_registry_record('castle.aws_s3_host_endpoint', minio_bucket_endpoint)
            api.portal.set_registry_record('castle.aws_s3_base_url', minio_base_url)

        def tearDown(self):
            #os.system("""docker rm -f minio_castle_test""")
            pass

        def test_get_bucket(self):
            s3, bucket = aws.get_bucket("castletest")
            self.assertIsNotNone(s3)
            self.assertIsNotNone(bucket)

        def test_move_file(self):
            # upload a file
            self.request.form.update({
                'action': 'chunk-upload',
                'chunk': '1',
                'chunkSize': 1024,
                'totalSize': 1024 * 5,
                'file': BytesIO('X' * 1024),
                'name': 'foobar.bin'
            })
            cc = content.Creator(self.portal, self.request)
            data = json.loads(cc())
            self.request.form.update({
                'id': data['id']
            })
            for idx in range(4):
                self.request.form.update({
                    'action': 'chunk-upload',
                    'chunk': str(idx + 2),
                    'file': BytesIO('X' * 1024)
                })
                cc = content.Creator(self.portal, self.request)
                data = json.loads(cc())
            fileOb = api.content.get(path='/file-repository/foobar.bin')

            # move it to s3
            self.assertFalse(hasattr(fileOb.file, 'original_filename'))
            self.assertFalse(hasattr(fileOb.file, 'original_size'))
            self.assertFalse(hasattr(fileOb.file, 'original_content_type'))
            aws.move_file(fileOb, disable_set_permission=True)
            fileOb = api.content.get(path='/file-repository/foobar.bin')
            self.assertTrue(hasattr(fileOb.file, 'original_filename'))
            self.assertTrue(hasattr(fileOb.file, 'original_size'))
            self.assertTrue(hasattr(fileOb.file, 'original_content_type'))

else:
    class TestEmptyAWS(unittest.TestCase):
        layer = CASTLE_PLONE_FUNCTIONAL_TESTING

        def test_dummy(self):
            pass
