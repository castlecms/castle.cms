from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from zope import schema
from zope.component import queryUtility
from zope.interface import alsoProvides

import json


class SiteConfiguration:
    def __call__(self):
        form = self.request.form

        alsoProvides(self.request, IDisableCSRFProtection)
        self.request.response.setHeader('Content-type', 'application/json')

        registry = queryUtility(IRegistry)

        try:
            for field in form:
                if field in registry:

                    schema_field = registry.records[field]._field

                    fieldValue = form.get(field)
                    value = None

                    if isinstance(schema_field, schema.Bool):
                        # JSON doesn't want to convert them back to boolean
                        if fieldValue == 'true':
                            value = True
                        elif fieldValue == 'false':
                            value = False

                    elif isinstance(schema_field, schema.TextLine):
                        value = unicode(fieldValue)

                    elif isinstance(schema_field, schema.ASCII):
                        value = str(fieldValue)

                    else:
                        continue

                    registry[field] = value

            return json.dumps({
                'success': True,
                'start': self.context.absolute_url()
            })
        except Exception:
            return json.dumps({
                'success': False,
                'errors': "There was a problem setting your configurations",
                'start': self.context.absolute_url()
            })
