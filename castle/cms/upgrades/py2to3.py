import os

import castle.cms
from plone import api
from Products.GenericSetup.context import DirectoryExportContext


def post_handler(context):
    '''
    cleanup exported catalog
    '''
    profile_path = os.path.join(
        os.path.dirname(os.path.realpath(castle.cms.__file__)),
        'profiles/py2to3'
    )
    catalog_xml_path = os.path.join(profile_path, 'catalog.xml')
    os.remove(catalog_xml_path)


def pre_handler(context):
    '''
    1. export current portal_catalog
    2. move exported catalog to py2to3 location
    2. delete current portal_catalog
    '''
    ps = api.portal.get_tool('portal_setup')
    handler = ps.getExportStep('catalog')
    profile_path = os.path.join(
        os.path.dirname(os.path.realpath(castle.cms.__file__)),
        'profiles/py2to3'
    )
    context = DirectoryExportContext(ps, profile_path)
    handler(context)

    profile_path = os.path.join(
        os.path.dirname(os.path.realpath(castle.cms.__file__)),
        'profiles/py2to3'
    )
    catalog_xml_path = os.path.join(profile_path, 'catalog.xml')
    with open(catalog_xml_path, 'r') as fi:
        txt = fi.read()
    txt = txt.replace('DateRecurringIndex', 'DateIndex')
    with open(catalog_xml_path, 'w') as fi:
        fi.write(txt)

    site = api.portal.get()
    site.manage_delObjects(['portal_catalog'])
