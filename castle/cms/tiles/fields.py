from castle.cms import utils
from castle.cms.behaviors.location import ILocation
from castle.cms.interfaces import IFieldTileRenderer
from castle.cms.interfaces import IVersionViewLayer
from datetime import datetime
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.dexterity.behaviors.metadata import IDublinCore
from plone.app.dexterity.behaviors.metadata import IOwnership
from plone.app.dexterity.behaviors.metadata import IPublication
from plone.app.relationfield.behavior import IRelatedItems
from plone.app.standardtiles.field import DexterityFieldTile as BaseDexterityFieldTile
from plone.app.textfield.value import RichTextValue
from plone.autoform.view import WidgetsView
from plone.memoize.view import memoize_contextless
from plone.namedfile.file import NamedBlobImage
from plone.tiles import Tile
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.field import Fields
from zope.component import getMultiAdapter
from zope.component import queryUtility


# optimize lookups
_supported_schemas = {
    'IDublinCore': IDublinCore,
    'IOwnership': IOwnership,
    'IPublication': IPublication,
    'IRelatedItems': IRelatedItems,
    'ILeadImage': ILeadImage,
    'ILocation': ILocation
}


class DexterityFieldTile(BaseDexterityFieldTile):
    default_template = ViewPageTemplateFile('templates/fields/default.pt')
    image_template = ViewPageTemplateFile('templates/fields/image.pt')
    default_timezone = None

    @property
    @memoize_contextless
    def utils(self):
        return getMultiAdapter((self.context, self.request),
                               name="castle-utils")

    def __init__(self, context, request):
        if IVersionViewLayer.providedBy(request):
            version = request.form.get('version')
            context = utils.get_object_version(context, version)
        Tile.__init__(self, context, request)
        WidgetsView.__init__(self, context, request)

        try:
            self.schema_name, _, self.field_name = self.data['field'].partition('-')
        except KeyError:
            self.field = self.field_name = self.schema_name = None
            return

        if self.schema_name in _supported_schemas:
            schema = _supported_schemas[self.schema_name]
            self.field = '%s.%s' % (self.schema_name, self.field_name)
            self.fields += Fields(
                schema,
                prefix=self.schema_name
            ).select(self.field)
            self._additionalSchemata = (schema,)
        else:
            super(DexterityFieldTile, self).__init__(context, request)

    def __call__(self):
        if self.field and self.isVisible:
            renderer = queryUtility(IFieldTileRenderer, self.field + '-renderer')
            if renderer:
                self.field_value = renderer(self)
            else:
                self.update()
                widget = self.widgets.get(self.field)
                if hasattr(widget, '_converter'):
                    self.field_value = widget._converter(
                        widget.field, self).toFieldValue(widget.value)
                else:
                    if widget is None:
                        if hasattr(self.context, self.field):
                            self.field_value = getattr(self.context, self.field)
                        else:
                            self.field_value = ''  # default here...
                    else:
                        self.field_value = widget.value

            if 'className' not in self.data:
                className = ''
                if self.field_name == 'title':
                    className = 'documentFirstHeading'
                elif self.field_name == 'description':
                    className = 'documentDescription'
                self.data['className'] = className
            if 'tag' not in self.data:
                tag = 'div'
                if self.field_name == 'title':
                    tag = 'h1'
                self.data['tag'] = tag

            if isinstance(self.field_value, datetime):
                self.field_value = self.utils.format_date(
                    self.field_value, self.data.get('format', 'notime'))
            elif isinstance(self.field_value, RichTextValue):
                self.field_value = self.field_value.output
            elif isinstance(self.field_value, list):
                self.field_value = '<br />'.join(self.field_value)
            elif isinstance(self.field_value, NamedBlobImage):
                return self.image_template()
            return self.default_template()
        return u'<html></html>'


def LocationsFieldRenderer(view):
    return view.utils.get_locations(view.context)
