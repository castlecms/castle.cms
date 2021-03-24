from castle.cms.interfaces import ITemplate
from zope.component.hooks import getSite
from zope.interface import alsoProvides


def save_as_template(obj, event):
    alsoProvides(obj, ITemplate)
    site = getSite()
    try:
        site.templates.append(obj)
    except AttributeError:
        site.templates = [obj]

    import pdb; pdb.set_trace()

    # If all goes well, reset this so don't create new template each save.
    obj.convert_object_to_template = False


def get_templates():
    pass
