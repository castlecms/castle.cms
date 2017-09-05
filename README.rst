.. image:: https://www.wildcardcorp.com/logo.png
    :height: 50
    :width: 382
    :alt: Original work by wildcardcorp.com
    :scale: 50 %


For access to CastleCloud, our hosted CastleCMS service, or to request customizations and demos, please contact us at https://castlecms.io or https://wildcardcorp.com

info@wildcardcorp.com

+1 (715) 869-3440

=======================================
Welcome to the main Castle CMS package!
=======================================


Feature List
============

In addition to Plone standard features...

- Login/lockout support
- Content archival to Amazon S3 Storage
- Large files automatically moved to S3 storage
- Redis cache support
- Advanced content layout editor
- Improved management toolbar
- Intuitive content creation and organization
- Elasticsearch integration
- Search results are tuned by social media impact
- Search result pinning
- Celery task queue integration (asynchronous actions)
    - PDF generation
    - Video conversion
    - Amazon S3 interaction
    - copying and pasting of large batches of items
    - deletion of large batches of items
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
- Disqus integration
- reCAPTCHA integration
- fullcalendar integration
- Business metadata
- Emergency notification system with SMS support
- Preview content
- Map content
- KML feeds
- Social media integration with
    - Twitter, Facebook, Pinterest
- Etherpad collaborative spaces support
- Stripping metadata from files
- Ability to view the site as another user
- Audit log, user activity reports
- Session management and inspection
- Analytics dashboard
- De-duplication of uploaded images
- Trash can / recycle bin
- 2-factor authentication


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
5. ``bin/pip install -r requirements.txt``
6. ``bin/buildout``
7. Run ``elasticsearch``, ``redis-server``, ``bin/instance fg`` and ``bin/celery worker``
8. Go to http://localhost:8080/


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

Assuming you have buildout properly installed to run the tests:

.. code-block:: shell

    Xvfb :99 &
    Xvfb :99 -fp /usr/share/X11/fonts/misc -screen 0 1900x1900x24 &
    export DISPLAY=:99

To access the running Selenium test server on port 55001:

.. code-block:: shell

    ZSERVER_HOST=0.0.0.0 ./bin/test -s castle.cms

To specify custom Firefox binary to match versions:

.. code-block:: shell

    FIREFOX_BINARY=/opt/firefox/firefox ./bin/test  -s castle.cms

Non-Selenium tests:

since selenium can be flaky...

.. code-block:: shell

  ./bin/test -s castle.cms -t \!selenium


Google Analytics Key File
-------------------------

- go to the Google API console
- create new credentials
  - service account
  - p12
- enable Analytics API api for credentials
- fill out email with email provided and p12 file in Castle API settings
- use email for email you want to access and add it as an authorized user for the account in Google Analytics


Cron jobs
=========

Castle uses many cron jobs that need to be setup.

Daily
-----

- ``bin/clean-plone-users``: removes disabled users
- ``bin/social-counts``: goes through all content and updates social media counts. Can be done monthly
- ``bin/content-popularity``: if GA setup, will get content statistics for popularity

Weekly
------

- ``bin/archive-content``: Archive content and send out content warnings about content that will be archived
- ``bin/empty-trash``: Delete items that have been in trash for 30 days
- ``bin/send-forced-publish-alert``: Send update to admins about content that was forced published


Processes
---------

- ``bin/twitter-monitor``: Monitor Twitter for mentions of your site



Export/Import
-------------

Castle provides a simple export/import mechanism that does not use transmogrifier.

You are still able to build your own custom transmogrifier pipelines to import/export
into castle; however, our scripts seem to work in a lot of cases to get your
content moved over to start working with.


Export
~~~~~~

Copy the export script into your existing site's main buildout folder of your site::

  https://raw.githubusercontent.com/castlecms/castle.cms/master/castle/cms/_scripts/export-content.py

Then, to run the export script::

  ./bin/client1 run export-content.py --site-id=mysiteid --dir=./export

This is assuming that "client1" is an instance of your site and "mysiteid" is the
id of your install plone site.

To customize the export script so only parts of the site are exported,
you can change the final line in the script to a custom catalog query that only
pulls in the content you want to export.


Import
~~~~~~

First off, copy the exported directory that you did in the previous step to
the castle installation folder.

Next, copy the import script into your new castle site's main buildout folder::

  https://raw.githubusercontent.com/castlecms/castle.cms/master/castle/cms/_scripts/importjson.py

Then, to run the import script::

  ./bin/client1 run importjson.py --site-id=mysiteid --export-directory=./export

This is assuming that "client1" is an instance of your site and "mysiteid" is the
id of your install plone site.


To register your own import type(Event example)::

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

There are a few different tiles that castle provides that allow you to customize
the display type. The display type field is a way of providing a different
view onto the content.

Available display type tiles(listing with display type vocab id):

 - Navigation(navigation)
 - Existing content(existing)
 - Gallery(gallery)
 - Query Listing(querylisting)


Providing your own display types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are 3 components to registering a display type for a tile:
  - Display type class
  - Page template
  - ZCML registration

I know, probably too much but not a lot of thought has gone into how to make
this more simple for the developer at this point.


Example custom display type
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We'll go through an example for the existing content tile

Display type class::

    class MyTileView(BaseTileView):
        name = 'myview'
        preview = '++plone++castle/path/to/image.png'
        order = 1
        index = ViewPageTemplateFile('myview.pt')
        tile_name = 'existing'


Then, the template::

    <tal:wrap tal:define="utils view/tile/utils;
                          data view/tile/data;
                          df view/tile/display_fields;
                          idt data/image_display_type|string:landscape;
                          existing nocall: view/tile/content|nothing;
                          url python: utils.get_object_url(existing);
                          has_image python: 'image' in df and utils.has_image(existing);">
     <h3><a href="${url}">${existing/Title}</a></h3>
    </tal:wrap>


Finally, the ZCML to register it::

    <adapter
      name="existing.myview"
      provides="castle.cms.interfaces.ITileView"
      for="plone.dexterity.interfaces.IDexterityContent castle.cms.interfaces.ICastleLayer"
      factory=".myview.MyTileView"
      />



Lead images
-----------

- all content has lead images
- lead images can be references to other images on the site



Castle upgrades
---------------

Right now, there is no way that is exposed nicely in site setup to run castle
upgrades.

To run upgrades::

  - go to /manage on your plone site
  - Then, portal_setup
  - click the "Upgrades" tab
  - select "castle.cms:default" and click "choose profile"
  - from here, you should get a list of available upgrades to run


After the deadline
------------------

Castle integrates with Plone's basic tinymce after the deadline support to::

  - also support after the deadline in rich text tiles
  - integrate spelling/grammar check with content quality check

To utilize after the deadline integration, configure after the deadline in the
plone tinymce configuration panel and castle will pay attention to the settings
selected there.

After the deadline
------------------
To enable 2 level navigation delete the following line::
  <ul class="nav navbar-nav" data-tile="${portal_url}/@@fragment?name=mainlinks"></ul>

Add the following line in its place ::
  <div data-tile="${context_url}/@@castle.cms.twolevelnav"></div>
