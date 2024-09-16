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

import os
import re
import argparse
import shutil
import uuid
import logging
import transaction
import Globals

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='...')
parser.add_argument('--site-id', dest='site_id', default='Plone') # Default should be 'Castle' 
parser.add_argument('--object-path', dest='object_path', default='/Plone/news/blog')
args, _ = parser.parse_known_args()

app = app  # noqa


def generate_new_id(object_id, object_path):
    """
    Returns a new id formatted in the same way as a copy/pasted item

    i.e. copy1_of_item
    
    """

    # Regular expression to find the number suffix
    pattern = re.compile(r'^(.+?)_(\d*)$')
    
    # Extract base name and number, if any
    match = pattern.match(object_id)
    if match:
        base_name, num_str = match.groups()
        start = int(num_str) if num_str else 0
    else:
        base_name = object_id
        start = 0

    # Check for existing paths
    while True:
        if start == 0:
            new_id = base_name
        else:
            # Format id
            parts = base_name.split('_', 1)
            p1 = parts[0] + str(start)
            p2 = '_' + parts[1]
            new_id = '{}{}'.format(p1,p2)
        
        new_path = os.path.join(object_path, new_id)
        
        # Check if the item exists
        obj = site.restrictedTraverse(new_path.strip('/'), None)
        if obj is None:
            return new_id
        
        start += 1


def duplicate_content(site, object_path):
    """
    Export a Zope/Plone object to a .ZEXP file, modify the existing DB entity,
        then re-import it from the file.
    This is useful for duplicating large items that slow down or break the
        normal copy/paste process.
    
    :param site: Plone site id.
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
        # Move file to 'import' directory
        file_name = str(obj.id) + '.zexp'
        base_path = os.path.dirname(Globals.data_dir)
        og_path = os.path.join(base_path, 'instance', file_name)

        if not os.path.exists(og_path):
            logger.error("File does not exist: '{}' ".format(og_path))
            return

        file_name = str(obj.id) + '.zexp'
        export_path = os.path.join(base_path, 'instance', 'import')
        exported_file = os.path.join(export_path, file_name)

        if os.path.exists(exported_file):
            os.remove(exported_file)
    
        shutil.move(og_path, export_path)

    except shutil.Error as e:
        logger.error("Error moving file: {}".format(e))
        return
    except Exception as e:
        logger.error("Unexpected error: {}".format(e))
        return

    try:
        # Assign new UUID to existing item
        new_uuid = uuid.uuid4().hex
        setattr(obj, ATTRIBUTE_NAME, new_uuid)
    except Exception as e:
        logger.error("Error setting new UUID: {}".format(e))
        return
    
    # Assign new id and unpublish
    util = queryUtility(IIDNormalizer)
    new_id = util.normalize('copy_of_' + obj.id)
    new_id = generate_new_id(new_id, object_path)
    # obj.title = obj.Title() + ' - Copy'
    api.content.transition(obj, to_state='private')

    try:
        api.content.rename(obj, new_id=new_id)
    except Exception as e:
        logger.error("Error renaming object to '{}': {}".format(new_id, e))
        return

    obj.reindexObject()
    transaction.commit()
    
    try:
        # Import original item back into Zope
        container.manage_importObject(file_name)
        transaction.commit()
        os.remove(exported_file)
    except Exception as e:
        print("Error importing file: {}".format(e))
        return


if __name__ == '__main__':
    login_as_admin(app)  # noqa
    site = app[args.site_id]  # noqa
    object_path = args.object_path
    if IPloneSiteRoot.providedBy(site):
        try:
            duplicate_content(site, object_path)
        except Exception:
            logger.error('Encountered error %s' % site, exc_info=True)
    else:
        logger.error('%s is not a site' % site)
