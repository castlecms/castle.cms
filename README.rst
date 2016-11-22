
Credit
------
For access to CastleCloud the hosted implementation, customizations, and demonstrations, please contact us at https://castlecms.io or https://wildcardcorp.com

info@wildcardcorp.com 
715.869.3440


.. image:: https://www.wildcardcorp.com/logo.png
   :height: 50
   :width: 382
   :alt: Original work by wildcardcorp.com
   :align: right
   


Overview
========

Welcome to the main Castle CMS package!

This package does a lot of customizations to default Plone and without an installer,
this package won't be very useful.

Until there is an installer, here are some of the things you'll need:

- use this version of plone.app.blocks: https://github.com/castlecms/plone.app.blocks
- Redis installed
- avconv installed(needs to be updated for ffmpeg again)
- ElasticSearch 2.3 installed
- https://github.com/castlecms/elasticsearch-castle-scoring installed
- https://github.com/castlecms/castlehps installed for faster search integration
- S3 credentials
- Google Analytics API integration
- Plivio API
- recaptcha key


Feature List
------------
In addition to Plone standard features...

- Login/Lockout support
- Content Archival to S3 Storage
- Large files automatically moved to s3 storage
- Redis cache support
- Advanced content layout editor
- Improved management toolbar
- Intuitive content creation and organization
- Elasticsearch integration
- Search results are influenced by social media impact
- Search result pinning
- Celery task queue integration(asynchrous actions)
    - PDF generation
    - Video conversation
    - S3 interaction
    - copy pasting large batches of items
    - deleting large batches of items
- Trash can
- Advanced content tiles:
    - maps
    - videos
    - audio
    - sliders
    - galleries
    - Table of contents
- Audio and Video content
- Automatic conversion of videos to web compatible format
- Search weighting based on popularity using google analytics API
- Content alias management
- Disqus integration
- recaptcha integration
- fullcalendar integration
- Business metadata
- Emergency notification system with SMS support
- Preview content
- map content
- KML feeds
- Social media integration with
    - twitter, facebook, pinterest
- etherpad collaborative spaces support
- strip metadata from files
- be able to view site as another user
- audit log, user activity reports
- session management and inspector
- analytics dashboard
- de-duplication of uploaded images
- recycle bin
- 2-factor auth


Running tests
-------------

Assuming you have buildout properly installed to run the tests...

Xvfb :99 &
Xvfb :99 -fp /usr/share/X11/fonts/misc -screen 0 1900x1900x24 &
export DISPLAY=:99

To access the running selenium test server on port 55001:

ZSERVER_HOST=0.0.0.0 ./bin/test -s castle.cms

To specify custom firefox binary to match versions...

FIREFOX_BINARY=/opt/firefox/firefox ./bin/test  -s castle.cms

Non selenium tests:

  ./bin/test -s castle.cms -t \!selenium


Google Analytics Key File
-------------------------

- Go to google api console
- create new credentials
  - service account
  - p12
- enable Analytics API api for credentials
- fill out email with email provided and p12 file in castle api settings
- use email for email you want to access and add it as an authorized user for the account
  in google analytics


Cron jobs
---------

Castle utilizes quite a few cron jobs that should be setup.

Daily
~~~~~~

 - bin/clean-plone-users: cleans disabled users
 - bin/social-counts: goes through all content and updates social media counts. Can be done monthly
 - bin/content-popularity: if GA setup, will get content statistics for popularity

Weekly
~~~~~~

  - bin/archive-content: Archive content and send out content warnings about content that will be archived
  - bin/empty-trash: Delete items that have been in trash for 30 days
  - bin/send-forced-publish-alert: Send update to admins about content that was forced published


Processes
~~~~~~~~~

  - bin/twitter-monitor: Monitor twitter for mentions of site
