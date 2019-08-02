from castle.cms.toolbar import BaseToolbarModifier
from collective.easyform.interfaces import IEasyForm
from collective.easyform.interfaces import IEasyFormLayer
from plone import api
from plone.schemaeditor.interfaces import IFieldContext
from plone.schemaeditor.interfaces import ISchemaContext


class ToolbarModifier(BaseToolbarModifier):
    """
    Add menu item to review migration
    """
    layer = IEasyFormLayer

    def __call__(self, result_menu, name, view):
        context = view.real_context
        if (name != 'toolbar_menu' or
                (len(result_menu) and result_menu[0]['id'] != 'view-page') or
                (not IFieldContext.providedBy(context) and
                    not ISchemaContext.providedBy(context))):
            return result_menu

        # find easyform context
        count = 0
        while not IEasyForm.providedBy(context):
            try:
                context = context.__parent__
            except AttributeError:
                context = api.portal.get()
                break
            count += 1
            if count > 20:
                # prevent getting stuck
                context = api.portal.get()
                break

        result_menu[0]['url'] = '{}/view'.format(context.absolute_url())
        return result_menu
