Migration
=========


CastleCMS provides a simple export/import mechanism that does not use transmogrifier.
The reasoning behind this is we wanted a single file to drop on existing servers to
export content(no need to run buildout and implement complex pipelines).

You are still able to build your own custom transmogrifier pipelines to import/export
into CastleCMS; however, our scripts work in a lot of cases to get your
content moved over quickly.


Export
------

Copy the export script into your existing site's main buildout folder::

  https://raw.githubusercontent.com/castlecms/castle.cms/master/castle/cms/_scripts/export-content.py

Then, to run the export script::

  ./bin/client1 run export-content.py --site-id=mysiteid --dir=./export

where "client1" is a ZEO client of your site and "mysiteid" is the
ID of your Plone site.

To customize the export script so only parts of the site are exported,
you can change the final line in the script to a custom catalog query that 
pulls in only the content you want to export.


Import
------

Start by copying the exported directory (that you created in the previous step) to
the CastleCMS installation folder.

Next, copy the import script into your new CastleCMS site's main buildout folder::

  https://raw.githubusercontent.com/castlecms/castle.cms/master/castle/cms/_scripts/importjson.py

Then, to run the import script::

  ./bin/client1 run importjson.py --site-id=mysiteid --export-directory=./export

where "client1" is a ZEO client of your site and "mysiteid" is the
ID of your CastleCMS site.


To register your own import type, using Event as an example::

    from castle.cms._scripts.importtypes import BaseImportType
    from castle.cms._scripts.importtypes import register_import_type
    from castle.cms._scripts.importtypes import DateTime_to_datetime

    class MyImportType(BaseImportType):
        fields_mapping = {
            # list of original field names to new field names
            # 'startDate': 'start'
        }
        data_converters = {
            # field name -> func(val) -> val
            # convert data to the format it should be
            # 'start': DateTime_to_datetime,
        }
        behavior_data_mappers = (
            # (Behavior Interface, field name)
            # to set behavior data from export data...
            # (IEventBasic, 'start'),
        )

        def post_creation(self, obj):
            '''
            Additional custom data migration after object is created
            ''''
            super(MyType, self).post_creation(obj)
            obj.foo = 'bar'

    register_import_type('MyType', MyImportType)