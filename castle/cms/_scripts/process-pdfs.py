import argparse
import transaction
import tempfile
import logging
import shutil
import os

from zope.component.hooks import setSite
from castle.cms.commands import exiftool
from castle.cms.commands import qpdf
from castle.cms.commands import gs_pdf
from plone.namedfile.file import NamedBlobFile

# PDFs uploaded to CastleCMS 2.5.9 or earlier might have unwanted metadata
# Run this to reprocess them

logger = logging.getLogger('castle.cms')

parser = argparse.ArgumentParser(
    description='...')
parser.add_argument('--site-id', dest='site_id', default='Castle')

args, _ = parser.parse_known_args()

site = app[args.site_id]  # noqa
setSite(site)


def process_PDFs():
    cat = site.portal_catalog
    filebrains = cat(portal_type='File', contentType='application/pdf')
    print('Processing {} PDFs'.format(len(filebrains)))
    count = 0
    for brain in filebrains:
        obj = brain.getObject()
        blob = obj.file.open('r')
        tmp_dir = tempfile.mkdtemp()
        filepath = os.path.join(tmp_dir, obj.file.filename).encode('utf-8').strip()
        file = open(filepath, 'wb')
        file.write(blob.read())
        file.close()
        blob.close()
        try:
            gs_pdf(filepath)
        except Exception:
            logger.warn(u'Could not strip additional metadata with gs {}'.format(filepath), exc_info=True)  # noqa
        try:
            exiftool(filepath)
        except Exception:
            logger.warn(u'Could not strip metadata with exiftool {}'.format(filepath), exc_info=True)  # noqa
        try:
            qpdf(filepath)
        except Exception:
            logger.warn(u'Could not strip additional metadata with qpdf {}'.format(filepath), exc_info=True)  # noqa
        file = open(filepath, 'rb')
        obj.file = NamedBlobFile(file, filename=obj.file.filename)
        file.close()
        shutil.rmtree(tmp_dir)
        count += 1
        if count % 50 == 0:
            print('Processed {} PDFs'.format(count))
            transaction.commit()
    transaction.commit()
    print('Done.')


if __name__ == '__main__':
    process_PDFs()
