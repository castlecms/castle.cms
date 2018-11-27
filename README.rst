.. image:: https://www.wildcardcorp.com/logo.png
    :height: 50
    :width: 382
    :alt: Original work by wildcardcorp.com
    :scale: 50 %


For access to Castle Cloud (our hosted CastleCMS service) or to request customizations or demos, please contact us at https://castlecms.io or https://wildcardcorp.com

info@wildcardcorp.com

+1 (715) 869-3440

=======================================
Welcome to the main CastleCMS package!
=======================================


Feature List
============

In addition to Plone standard features, CastleCMS includes:

- Login/lockout support
- Content archival to Amazon S3 storage
- Large files automatically moved to S3 storage
- Redis cache support
- Advanced content layout editor
- Improved management toolbar
- Intuitive content creation and organization
- Elasticsearch integration
- Search results tuned by social media impact
- Search results pinning
- Celery task queue integration (asynchronous actions)
    - PDF generation
    - Video conversion
    - Amazon S3 interaction
    - copying and pasting of large batches of items
    - deletion and renaming of large batches of items
- Advanced content tiles:
    - maps
    - videos
    - audio
    - sliders
    - galleries
    - table of contents
- Audio and video content
- Automatic conversion of videos to web compatible format
- Search weighting based on popularity using Google Analytics API
- Content alias management
- Disqus commenting integration
- reCAPTCHA integration
- fullcalendar integration
- Google Business metadata
- Emergency notification system with optional SMS support
- Preview content on a variety of device sizes
- Map content
- KML feeds
- Social media integration with Twitter, Facebook, Pinterest
- Etherpad collaborative spaces support
- Stripping metadata from files
- Ability to view the site as another user
- Audit log, user activity reports
- Session management, inspection and termination
- Analytics dashboard
- De-duplication of uploaded images and files
- Trash can / recycle bin
- Two factor authentication


Installation
============

This package includes a lot of customizations to default Plone and, without an installer,
getting it running is a bit tricky.

Dependencies
------------

- Redis
- avconv (needs to be updated for ffmpeg again)
- ElasticSearch 2.3


Development setup on macOS
--------------------------

1. ``brew install redis elasticsearch libav python``
2. ``git clone git@github.com:castlecms/castle.cms.git``
3. ``cd castle.cms``
4. ``virtualenv -p python2.7 .``
5. ``bin/pip install --upgrade pip``
6. ``bin/pip install -r requirements.txt``
7. ``bin/buildout``
8. Run (in separate terminal windows) ``elasticsearch``, ``redis-server``, ``bin/instance fg`` and ``bin/celery worker``
9. Browse to http://localhost:8080/


Optional Dependencies
---------------------

- Install `argon2_cffi` to use more secure password hashing.
- https://github.com/castlecms/elasticsearch-castle-scoring
- https://github.com/castlecms/castlehps for faster search integration
- Amazon S3 credentials to store large files on S3
- Google API keys for Google analytics and Recaptcha integrations
- Plivo API for SMS


Running tests
=============

Default plone testing:

.. code-block:: shell

  ./bin/test -s castle.cms

To run only robot tests:
.. code-block:: shell
  ./bin/test -s castle.cms -t robot


Without robot:
.. code-block:: shell
  ./bin/test -s castle.cms -t \!robot

If you have errors complaining about warning, make sure the version of selenium 
you're using works with the version of Firefox you have installed (see above)


Google Analytics Key File
-------------------------

- go to the Google API console
- create new credentials
  - service account
  - p12
- enable Analytics API api for credentials
- fill out email with email provided and p12 file in CastleCMS API settings
- use email for email you want to access and add it as an authorized user for the account in Google Analytics


Cron jobs
=========

CastleCMS uses many cron jobs that need to be setup.

Daily
-----

- ``bin/clean-plone-users``: removes disabled users
- ``bin/social-counts``: goes through all content and updates social media counts. Can be done monthly
- ``bin/content-popularity``: if Google Analytics is setup, will get content statistics for popularity
- ``bin/clean-drafts``: clean old draft data

Weekly
------

- ``bin/archive-content``: Archive content and send out warnings about content that will be archived
- ``bin/empty-trash``: Delete items that have been in trash for 30 days
- ``bin/send-forced-publish-alert``: Send update to admins about content that was forced-published


Processes
---------

- ``bin/twitter-monitor``: Monitor Twitter for mentions of your site
- ``bin/castle-crawler``: Crawl sites defined in crawler settings


Export/Import
-------------

CastleCMS provides a simple export/import mechanism that does not use transmogrifier.

You are still able to build your own custom transmogrifier pipelines to import/export
into CastleCMS; however, our scripts work in a lot of cases to get your
content moved over quickly.


Export
~~~~~~

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
~~~~~~

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



Tile display types
------------------

There are tiles provided by CastleCMS that allow you to customize
the display type. The display type field is a way of providing a different
view of the content.

Available display type tiles include the following (along with the matching display type vocabulary ID):

 - Navigation (navigation)
 - Existing content (existing)
 - Gallery (gallery)
 - Query Listing (querylisting)


Providing your own display types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are 3 components to registering a display type for a tile:
  - Display type class
  - Page template
  - ZCML registration

Example custom display type
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is an example of creating a custom display type for the existing content tile.

Define the display type class::

    class MyTileView(BaseTileView):
        name = 'myview'
        preview = '++plone++castle/path/to/image.png'
        order = 1
        index = ViewPageTemplateFile('myview.pt')
        tile_name = 'existing'


Then define the template::

    <tal:wrap tal:define="utils view/tile/utils;
                          data view/tile/data;
                          df view/tile/display_fields;
                          idt data/image_display_type|string:landscape;
                          existing nocall: view/tile/content|nothing;
                          url python: utils.get_object_url(existing);
                          has_image python: 'image' in df and utils.has_image(existing);">
     <h3><a href="${url}">${existing/Title}</a></h3>
    </tal:wrap>


Finally, define the ZCML to register it::

    <adapter
      name="existing.myview"
      provides="castle.cms.interfaces.ITileView"
      for="plone.dexterity.interfaces.IDexterityContent castle.cms.interfaces.ICastleLayer"
      factory=".myview.MyTileView"
      />



Lead images
-----------

- all content has lead images
- lead images can be references to other images on the site or to other content on the site that has a lead image



CastleCMS upgrades
-------------------

There is currently no UI in the Site Setup to run CastleCMS
upgrades.

To run upgrades::

  - go to the Management Interface (/manage) for your site
  - click on portal_setup
  - click the "Upgrades" tab
  - select "castle.cms:default" and click "choose profile"
  - from here, you should get a list of available upgrades to run


After the Deadline Spellchecking
--------------------------------

CastleCMS includes Plone's TinyMCE support for After the Deadline spellchecking and::

  - supports After the Deadline in rich text tiles
  - integrates spelling/grammar check within the content quality check dialog

To use After the Deadline, go to Site Setup and configure After the Deadline in the
TinyMCE configuration panel.



Building resources after changes to js
--------------------------------------

Just regular plone compile resources::

    ./bin/plone-compile-resources --site-id=Castle --bundle=plone
    ./bin/plone-compile-resources --site-id=Castle --bundle=plone-logged-in


Running local dependencies
--------------------------

    $ docker run -p 6379:6379 redis


Forks/Custom releases
---------------------

Castle maintains forks and custom releases of packages ocassionally. Here is the
status and reasoning for our forks:

- plone.app.blocks: https://github.com/castlecms/plone.app.blocks
  (Hard fork): Castle heavily customizes how Plone renders things including how "blocks" are rendered
- plone-app-mosaic: https://github.com/castlecms/plone.app.mosaic/tree/castlecms
  (Hard fork, castlecms branch): Originally for fixes but at this point, we will maintain the fork
  until we have reason not to or we have better alternative layout engines.
- plonetheme.barceloneta:
  (Hard fork): Castle rendering of barceloneta. No Diazo.
- plone.app.registry
  (Dev release): Release to get Plone 5.1 features into Castle based off Plone 5.0.
  Can be removed once we go to 5.2
- plone.app.standardtiles
  (Dev release): Unknown status on if we still need this release.
- Products.ZCatalog
  (Dev release): unknown status
- z3c.relationfield
  (Dev release): PR: https://github.com/zopefoundation/z3c.relationfield/pull/7
- mockup: https://github.com/plone/mockup/tree/2.4.x
  (Dev release): TinyMCE backport fixes from 5.1
- Products-CMFPlone
  (Dev release): TinyMCE backport fixes from 5.1 and bundle ordering bug: https://github.com/plone/Products.CMFPlone/pull/2632
