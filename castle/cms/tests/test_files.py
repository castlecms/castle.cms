# -*- coding: utf-8 -*-
import boto3
import botocore
from castle.cms.browser import content
import castle.cms.files.aws as aws
from castle.cms.files.duplicates import DuplicateDetector
from castle.cms.testing import (
    CASTLE_PLONE_INTEGRATION_TESTING,
    CASTLE_PLONE_FUNCTIONAL_TESTING,
)
from persistent.mapping import PersistentMapping
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.uuid.interfaces import IUUID
from moto import mock_s3
from zope.annotation.interfaces import IAnnotations

from io import BytesIO
import json
from time import time
import unittest
from urllib.parse import quote_plus


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
        api.content.transition(obj=doc, to_state='published')

        self.assertEqual(IUUID(dd.get_object(hash_)), IUUID(doc))


def upload_file_to_castle(self):
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
    return api.content.get(path='/file-repository/foobar.bin')


class TestAWS(unittest.TestCase):
    layer = CASTLE_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.test_access_key = u'AKIAIOSFODNN7EXAMPLE'
        self.test_secret_key = u'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        self.test_bucket_name = u'castletest'
        # possibly useful to set under some condition...
        # self.test_bucket_endpoint = u'http://localhost:9000/'
        self.test_base_url = u'https://localhost.localdomain/'  # used for test swap
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ('Member', 'Manager'))
        api.portal.set_registry_record('castle.aws_s3_key', self.test_access_key)
        api.portal.set_registry_record('castle.aws_s3_secret', self.test_secret_key)
        api.portal.set_registry_record('castle.aws_s3_bucket_name', self.test_bucket_name)
        # possibly useful to set under some condition...
        # api.portal.set_registry_record('castle.aws_s3_host_endpoint', self.test_bucket_endpoint)
        api.portal.set_registry_record('castle.aws_s3_base_url', self.test_base_url)

    def tearDown(self):
        pass

    @mock_s3
    def test_get_bucket(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3')
        s3conn.create_bucket(Bucket='castletest')

        s3, bucket = aws.get_bucket("castletest")
        self.assertIsNotNone(s3)
        self.assertIsNotNone(bucket)

    @mock_s3
    def test_move_file_private(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3')
        s3conn.create_bucket(Bucket='castletest')

        fileOb = upload_file_to_castle(self)

        s3, bucket = aws.get_bucket("castletest")
        uid = IUUID(fileOb)
        key = aws.KEY_PREFIX + uid

        # before move, there should be none of the meta information about the
        # moved version of the file
        self.assertFalse(hasattr(fileOb.file, 'original_filename'))
        self.assertFalse(hasattr(fileOb.file, 'original_size'))
        self.assertFalse(hasattr(fileOb.file, 'original_content_type'))

        # before move, there should be no annotations
        annotations = IAnnotations(fileOb)
        self.assertIsNone(annotations.get(aws.STORAGE_KEY, None))

        # before move, there should be no file in s3
        self.assertRaises(
            botocore.exceptions.ClientError,
            lambda: s3.meta.client.head_object(Bucket=bucket.name, Key=key))

        aws.move_file(fileOb)
        fileOb = api.content.get(path='/file-repository/foobar.bin')

        # after move, there should be additional meta information on the
        # file object
        self.assertTrue(hasattr(fileOb.file, 'original_filename'))
        self.assertTrue(hasattr(fileOb.file, 'original_size'))
        self.assertTrue(hasattr(fileOb.file, 'original_content_type'))

        # after move, there should be annotations on the object
        annotations = IAnnotations(fileOb)
        url = annotations[aws.STORAGE_KEY].get('url', None)
        expires_in = annotations[aws.STORAGE_KEY].get('expires_in', None)
        generated_on = annotations[aws.STORAGE_KEY].get('generated_on', None)
        self.assertIsNotNone(url)
        self.assertIsNotNone(expires_in)
        self.assertIsNotNone(generated_on)
        self.assertEqual(expires_in, aws.EXPIRES_IN)

        # after move, there should be no error from getting head information of
        # the uploaded object
        s3.meta.client.head_object(Bucket=bucket.name, Key=key)

    @mock_s3
    def test_move_file_public(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3')
        s3conn.create_bucket(Bucket='castletest')

        fileOb = upload_file_to_castle(self)

        api.content.transition(fileOb, 'publish')

        s3, bucket = aws.get_bucket("castletest")
        uid = IUUID(fileOb)
        key = aws.KEY_PREFIX + uid

        # before move, there should be none of the meta information about the
        # moved version of the file
        self.assertFalse(hasattr(fileOb.file, 'original_filename'))
        self.assertFalse(hasattr(fileOb.file, 'original_size'))
        self.assertFalse(hasattr(fileOb.file, 'original_content_type'))

        # before move, there should be no annotations
        annotations = IAnnotations(fileOb)
        self.assertIsNone(annotations.get(aws.STORAGE_KEY, None))

        # before move, there should be no file in s3
        self.assertRaises(
            botocore.exceptions.ClientError,
            lambda: s3.meta.client.head_object(Bucket=bucket.name, Key=key))

        aws.move_file(fileOb)
        fileOb = api.content.get(path='/file-repository/foobar.bin')

        # after move, there should be additional meta information on the
        # file object
        self.assertTrue(hasattr(fileOb.file, 'original_filename'))
        self.assertTrue(hasattr(fileOb.file, 'original_size'))
        self.assertTrue(hasattr(fileOb.file, 'original_content_type'))

        # after move, there should be annotations on the object
        annotations = IAnnotations(fileOb)
        url = annotations[aws.STORAGE_KEY].get('url', None)
        expires_in = annotations[aws.STORAGE_KEY].get('expires_in', None)
        generated_on = annotations[aws.STORAGE_KEY].get('generated_on', None)
        self.assertIsNotNone(url)
        self.assertIsNotNone(expires_in)
        self.assertIsNotNone(generated_on)
        self.assertEqual(expires_in, 0)

        # after move, there should be a file in s3, and checking for it should
        # produce no error
        s3.meta.client.head_object(Bucket=bucket.name, Key=key)

    @mock_s3
    def test_delete_file(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3')
        s3conn.create_bucket(Bucket='castletest')

        fileOb = upload_file_to_castle(self)

        s3, bucket = aws.get_bucket(s3_bucket='castletest')
        uid = IUUID(fileOb)
        key = aws.KEY_PREFIX + uid

        aws.move_file(fileOb)

        # before the delete operation, the file should exist
        # on s3, and this statement should not raise an exception
        s3.meta.client.head_object(Bucket=bucket.name, Key=key)

        aws.delete_file(uid)

        # after the delete operation, the file should not exist
        # on s3, but should still exist in plone (even if it
        # has no data...apparently...admittedly a place of possible
        # improvement?)
        self.assertRaises(
            botocore.exceptions.ClientError,
            lambda: s3.meta.client.head_object(Bucket=bucket.name, Key=key))

    @mock_s3
    def test_uploaded(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3')
        s3conn.create_bucket(Bucket='castletest')

        fileOb = upload_file_to_castle(self)

        self.assertFalse(aws.uploaded(fileOb))
        aws.move_file(fileOb)
        fileOb = api.content.get(path='/file-repository/foobar.bin')
        self.assertTrue(aws.uploaded(fileOb))

    @mock_s3
    def test_swap_url(self):
        awsurl = 'https://s3-us-gov-west-1.amazonaws.com/bucketname/archives/path/to/resource'
        baseurl = 'http://foo.com/'
        swappedurl = 'http://foo.com/archives/path/to/resource'

        resulturl = aws.swap_url(awsurl, base_url=baseurl)
        self.assertEqual(swappedurl, resulturl)

    @mock_s3
    def test_get_url_public_or_notexpired(self):
        # this is creating a bucket in the moto/mock s3 service
        bucket = 'castletest'
        s3conn = boto3.resource('s3')
        s3conn.create_bucket(Bucket=bucket)

        fileOb = upload_file_to_castle(self)
        api.content.transition(fileOb, 'publish')
        aws.move_file(fileOb)
        fileOb = api.content.get(path='/file-repository/foobar.bin')

        resulturl = aws.get_url(fileOb)
        # the url should be the configured base url (from configuration registry)
        # with the key appended to it.
        # the bucketname should not be a part of the url. this should be stripped.
        # the key should also be sent through quote_plus, which basically makes it
        # a single path segment... this is okay with boto3 and the aws s3 api, and
        # possibly recommended to make sure your key's are passed to the api safely.
        key = quote_plus(aws.KEY_PREFIX + IUUID(fileOb))
        # wrap this in str before decode because of futures import
        expectedurl = str(self.test_base_url + key).decode('utf-8')
        self.assertEqual(resulturl, expectedurl)

    @mock_s3
    def test_get_url_private_expired(self):
        # this is creating a bucket in the moto/mock s3 service
        s3conn = boto3.resource('s3')
        s3conn.create_bucket(Bucket='castletest')

        fileOb = upload_file_to_castle(self)
        aws.move_file(fileOb)
        fileOb = api.content.get(path='/file-repository/foobar.bin')

        # move the generated further into the past
        annotations = IAnnotations(fileOb)
        info = annotations.get(aws.STORAGE_KEY, PersistentMapping())
        newgeneratedon = time() - aws.EXPIRES_IN - 1000
        info.update({
            'generated_on': newgeneratedon,
        })
        annotations[aws.STORAGE_KEY] = info

        resulturl = aws.get_url(fileOb)
        self.assertTrue(resulturl.startswith(self.test_base_url))

        fileOb = api.content.get(path='/file-repository/foobar.bin')
        annotations = IAnnotations(fileOb)
        info = annotations.get(aws.STORAGE_KEY, PersistentMapping())
        self.assertNotEqual(info["generated_on"], newgeneratedon)
        self.assertEqual(info["expires_in"], aws.EXPIRES_IN)
