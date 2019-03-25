from plone import api
import io


def post_handler(context):
    '''
    cleanup exported catalog
    '''


def pre_handler(context):
    '''
    1. export current portal_catalog
    2. move exported catalog to py2to3 location
    2. delete current portal_catalog
    '''
    ps = api.portal.get_tool('portal_setup')
    handler = ps.getExportStep('catalog')
    fi = io.StringIO()
    result = handler(fi)
    import pdb; pdb.set_trace()
