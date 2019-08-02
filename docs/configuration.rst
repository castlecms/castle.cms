Configuration and deployment
============================


Cron jobs
---------

CastleCMS uses many cron jobs that need to be setup to provide functionality.


Daily
~~~~~

- ``bin/clean-plone-users``: removes disabled users
- ``bin/social-counts``: goes through all content and updates social media counts.
  Can be done at any interval. With changes/restrictions to various social media APIs,
  this is becoming less useful.
- ``bin/content-popularity``: if Google Analytics is setup, will get content statistics
  for popularity to help search ranking.
- ``bin/clean-drafts``: clean old draft data


Weekly
~~~~~~

- ``bin/archive-content``: Archive content and send out warnings about content
  that will be archived. Requires site configuration and S3 configuration.
- ``bin/empty-trash``: Delete items that have been in trash for 30 days
- ``bin/send-forced-publish-alert``: Send update to admins about content that was
  forced-published
- ``bin/link-report``: Scan public site urls and find broken links.


Processes
---------

Persistent processes that can run continuously(for example with supervisor)

- ``bin/twitter-monitor``: Monitor Twitter for mentions of your site. Requires working
  twitter configuration.
- ``bin/castle-crawler``: Crawl sites defined in crawler settings


Additional commands
-------------------

- ``bin/reindex-elasticsearch``: Reindex all content in elasticsearch
- ``bin/upgrade-sites``: Run all available upgrades on all sites


Google Analytics API Key File
-----------------------------

To integrate with Google Analytics reporting, you'll need to get an API key file.

- go to the Google API console
- create new credentials
  - service account
  - p12
- enable Analytics API api for credentials
- fill out email with email provided and p12 file in CastleCMS API settings
- use email for email you want to access and add it as an authorized user for the account in Google Analytics


Environment variables
---------------------

- BROKER_URL: celery broker url configuration
- CELERY_TASK_ALWAYS_EAGER: useful celery configuration to run tasks inline
- REDIS_SERVER: redis server host:port configuration
- LINK_REPORT_DB: db configuration string for link report
- TWITTER_CLIENT_KEY: twitter oauth client id
- TWITTER_CLIENT_SECRET: twitter oauth client secret
- GOOGLE_CLIENT_ID: google oauth client id
- GOOGLE_CLIENT_SECRET: google oauth client secret


Defaults
~~~~~~~~

Some defaults settings can be overridden with environment variables.
These are the supported ones:

- DEFAULT_IMAGE_TILE_SCALE: scale used for image tile(large)
- DEFAULT_IMAGE_TILE_DISPLAYTYPE: display type used for image tile(fullwidth)
- DEFAULT_EXISTING_TILE_IMAGE_DISPLAYTYPE: display type used for image(landscape)
- DEFAULT_EXISTING_TILE_DISPLAYTYPE: display type used for content(default)
- DEFAULT_GALLERY_TILE_DISPLAYTYPE: display type used for gallery(default)
- DEFAULT_QUERYLISTING_TILE_SORT_ON: default sorting for query listing tile(effective)
- DEFAULT_QUERYLISTING_TILE_DISPLAYTYPE: display type used for query listing(default)
- DEFAULT_VIDEO_TILE_AUTOPLAY: if video should auto play by default(false)
- DEFAULT_VIDEO_TILE_LOOP: if video should loop by default(false)
- DEFAULT_VIDEO_TILE_DISPLAYTYPE: display type of file(landscape)


