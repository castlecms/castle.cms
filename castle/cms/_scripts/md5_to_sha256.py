import argparse
import hashlib
import logging

from castle.cms.files import aws
from castle.cms.services.google.youtube import get_youtube_service
import plone.api as api
from zope.component.hooks import setSite


logger = logging.getLogger(__name__)
RESOURCES_KEY_PREFIX = 'archiveresources/'

parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Castle')
args, _ = parser.parse_known_args()


def update_s3_resources():
    bucket_name = api.portal.get_registry_record(
        'castle.aws_s3_bucket_name')
    s3_conn, bucket = aws.get_bucket(s3_bucket=bucket_name)
    objects_summary_list =  bucket.objects.all()
    for object_summary in objects_summary_list:
        md5_key = object_summary.key
        obj = s3_conn.get_object(key=md5_key)
        fidata = obj.get('Body')
        copy_source = {
            'Bucket': bucket.name,
            'Key': md5_key
        }
        sha256 = hashlib.sha256(fidata).hexdigest()
        sha256_content_path = '{0}{1}/{2}/{3}/{4}'.format(
            RESOURCES_KEY_PREFIX, sha256[0], sha256[1], sha256[2], sha256
        )
        try:
            # check if the key already exists
            bucket.Object(sha256_content_path).load()
            logger.info(f'key {md5_key} already exists, skipping')
        except botocore.exceptions.ClientError:
            # this is what we want, the sha256 hashed version shouldn't exist yet
            new_obj = bucket.Object(sha256_content_path)
            resp_copy = new_obj.copy(copy_source)
            if resp_copy.status == 200:
                resp_delete = bucket.Object(md5_key).delete()
                if resp_delete.status != 200:
                    logger.error(f'Unable to delete md5 hashed key {md5_key}. This key should not be used for security purposes')
                    raise Exception(f'Unable to delete key {md5_key}.')

if __name__ == '__main__':
    site = app[args.site_id]  # noqa
    setSite(site)
    update_s3_resources(site)
