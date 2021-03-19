from castle.cms.interfaces import ITemplate
from Products.Five.utilities.marker import mark


def save_as_template(obj, event):
    '''
    1. object gets added to template repository folder
    2. make object unpublishable
    3. object gets added to template tab on 'Add' content modal
    '''
    import pdb; pdb.set_trace()

    if ITemplate.providedBy(obj):
        pass
    else:
        mark(obj, ITemplate)

    # If all goes well, reset these values so don't create new template each save.
    obj.convert_object_to_template = False
    obj.template_name = ''
