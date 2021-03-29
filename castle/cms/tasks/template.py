from castle.cms import utils
from castle.cms.interfaces import ITemplate
from zope.component.hooks import getSite
from zope.interface import alsoProvides


def save_as_template(obj, event):
    '''
    - Make the original object unpublishable after being added
    '''
    site = getSite()
    folder = utils.recursive_create_path(site, '/templates')

    alsoProvides(obj, ITemplate)
    folder.append(obj)

    # If all goes well, reset this so don't create new template each save.
    obj.convert_object_to_template = False
