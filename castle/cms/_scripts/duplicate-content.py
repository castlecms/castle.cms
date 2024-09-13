# -*- coding: utf-8 -*-
from plone import api
from plone.i18n.normalizer.interfaces import IIDNormalizer
from zope.component import queryUtility
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from plone.uuid.interfaces import ATTRIBUTE_NAME  # noqa: E402
from Acquisition import aq_parent

from castle.cms.cron.utils import login_as_admin
from castle.cms.cron.utils import setup_site

import Globals
import logging
import os
import argparse
import shutil
import uuid
import transaction

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone') # Default should be 'Castle' 
parser.add_argument('--object-path', dest='object_path', default='/Plone/news/blog')
args, _ = parser.parse_known_args()

app = app  # noqa


def export_zexp(site, object_path):
    """
    Export a Zope/Plone object to a ZEXP file.
    
    :param site: Plone site object.
    :param object_path: Path of the object within Zope to export.
    """

    setup_site(site)

    try:
        # Get the object to export
        obj = site.restrictedTraverse(object_path.strip('/'), None)
        if obj is None:
            logger.error("Object not found: '{}'".format(object_path))
            return
    except Exception as e:
        logger.error("Error retrieving object: {}".format(e))
        return

    # Get parent directory of object
    container = aq_parent(obj)
    
    try:
        # Export original object as .zexp (automatically goes to '/var/instance')
        container.manage_exportObject(obj.id)
    except Exception as e:
        logger.error("Error exporting object: {}".format(e))
        return

    try:
        # Move to 'import' directory
        file = str(obj.id) + '.zexp'
        base_path = '/'.join(Globals.data_dir.split('/')[:-1])
        og_path = base_path + '/instance/' + file

        if not os.path.exists(og_path):
            logger.error("File does not exist: '{}' ".format(og_path))
            return

        export_path = base_path + '/instance/import'
        shutil.move(og_path, export_path)

    except shutil.Error as e:
        logger.error("Error moving file: {}".format(e))
        return
    except Exception as e:
        logger.error("Unexpected error: {}".format(e))
        return

    try:
        # Change UUID of existing item
        new_uuid = uuid.uuid4().hex
        setattr(obj, ATTRIBUTE_NAME, new_uuid)
    except Exception as e:
        logger.error("Error setting new UUID: {}".format(e))
        return
    
    # Change name and unpublish existing item
    util = queryUtility(IIDNormalizer)
    new_id = util.normalize(obj.id + '-copy')
    new_title = obj.Title() + ' Copy'
    obj.title = new_title
    api.content.transition(obj, to_state='private')

    try:
        api.content.rename(obj, new_id=new_id)
    except Exception as e:
        logger.error("Error renaming object to '{}': {}".format(new_id, e))
        return

    obj.reindexObject()

    try:
        transaction.commit()
    except Exception as e:
        logger.error("Error committing transaction: {}".format(e))
    
    try:
        # Import back into Zope
        # container._importObjectFromFile(import_path, verify=0, set_owner=1)
        container.manage_importObject(file)
        transaction.commit()
    except Exception as e:
        print("Error importing file: {}".format(e))
        return


if __name__ == '__main__':
    login_as_admin(app)  # noqa
    site = app[args.site_id]  # noqa
    object_path = args.object_path
    if IPloneSiteRoot.providedBy(site):
        try:
            export_zexp(site, object_path)
        except Exception:
            logger.error('Encountered error %s' % site, exc_info=True)
    else:
        logger.error('%s is not a site' % site)
