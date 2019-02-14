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
8. Run (in separate terminal windows) ``elasticsearch``, ``redis-server``, ``bin/instance fg``
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


Running local dependencies with docker
--------------------------------------

    $ docker run -p 6379:6379 redis
    $ docker run -p 9200:9200 elasticsearch:2.3.5


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
