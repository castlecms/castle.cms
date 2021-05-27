from castle.cms import utils
from castle.cms.interfaces import ITemplate
from plone import api
from zope.component.hooks import getSite
from zope.interface import alsoProvides


def save_as_template(obj, action):
    site = getSite()
    folder = utils.recursive_create_path(site, '/template-repository')
    folder.exclude_from_nav = True
    if action == 'convert':
        template_obj = api.content.move(source=obj, target=folder)
    elif action == 'copy':
        template_obj = api.content.copy(source=obj, target=folder)

    alsoProvides(template_obj, ITemplate)

    try:
        site.template_list.append(template_obj)
    except AttributeError:
        site.template_list = [template_obj]

    return template_obj
