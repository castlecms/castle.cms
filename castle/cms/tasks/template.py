from castle.cms import utils
from zope.container.interfaces import INameChooser

import plone.api as api


def _get_new_template_id(original_object, title):
    chooser = INameChooser(_get_template_folder())
    return chooser.chooseName(title, original_object)


def _get_template_folder():
    folder = utils.recursive_create_path(
        api.portal.get(),
        '/template-repository',
    )
    folder.exclude_from_nav = True
    return folder


def _set_title(obj, title):
    obj.setTitle(title)
    obj.reindexObject()


def move_to_templates(original_object, new_title):
    new_object = api.content.move(
        source=original_object,
        target=_get_template_folder(),
        id=_get_new_template_id(original_object, new_title),
        safe_id=True,
    )
    _set_title(new_object, new_title)
    return new_object


def copy_to_templates(original_object, new_title):
    new_object = api.content.copy(
        source=original_object,
        target=_get_template_folder(),
        id=_get_new_template_id(original_object, new_title),
        safe_id=True,
    )
    _set_title(new_object, new_title)
    return new_object
