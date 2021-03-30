from castle.cms import utils
from castle.cms.interfaces import ITemplate
from plone import api
from plone.locking.interfaces import ILockable
from zope.component.hooks import getSite
from zope.interface import alsoProvides


def save_as_template(obj):
    alsoProvides(obj, ITemplate)

    # Reset this so don't create new template each save.
    obj.convert_object_to_template = False


def move_template_to_repository(obj):
    site = getSite()
    folder = utils.recursive_create_path(site, '/template-repository')
    lockable = ILockable(obj)
    if lockable:
        lockable.clear_locks()
    api.content.move(source=obj, target=folder)

    try:
        site.template_list.append(obj)
    except AttributeError:
        site.template_list = [obj]
