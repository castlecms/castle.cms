.. image:: https://www.wildcardcorp.com/logo.png
    :height: 50
    :width: 382
    :alt: Original work by wildcardcorp.com
    :scale: 50 %
|

For access to CastleCloud, our hosted CastleCMS service, or to request customizations and demos, please contact us at https://castlecms.io or https://wildcardcorp.com

info@wildcardcorp.com

+1 (715) 869-3440

=======================================
Welcome to the main Castle CMS package!
=======================================

This package includes a lot of customizations to default Plone and, without an installer,
this package won't be very useful.

Until there is an installer, here are some of the things you'll need:

- this version of plone.app.blocks: https://github.com/castlecms/plone.app.blocks
- this version of plone.app.registry: https://github.com/plone/plone.app.registry/pull/15
- Redis
- avconv (needs to be updated for ffmpeg again)
- ElasticSearch 2.3
- https://github.com/castlecms/elasticsearch-castle-scoring
- https://github.com/castlecms/castlehps installed for faster search integration
- Amazon S3 credentials
- Google Analytics API integration
- Plivo API
- reCAPTCHA key


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


Optional Dependencies
=====================

- install `argon2_cffi` to use more secure password hashing


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
