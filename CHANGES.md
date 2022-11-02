Changelog
=========

3.0.0b112 (2022-11-02)
----------------------

- move HISTORY.rst to CHANGES.md
- re-add dependency on collective.elasticsearch for use of IElasticSearchLayer in case
  a site has collective.elasticsearch installed as an add-on, ensuring, eg, that the 'search'
  view remains correctly overridden


3.0.0b111 (2022-08-16)
----------------------

- make sure searchabletext for additionalsearchabletext implementation is entirely generated with unicode strings


3.0.0b110 (2022-08-08)
----------------------

- more forgiving coordinate parsing
- fix manifest.json credentials bug: added crossorigin="use-credentials"
- fixed WARNING plone.behavior Specifying 'for' in behavior 'Adjustable Font Size For Feature Tile' if no 'factory' is given has no effect and is superfluous.
- add GELF logging handler
- add script for generating user/role/permission reports
- remove 'reindex_es' script -- functionality is now in wildcard.hps
- remove 'upgrade_elasticsearch_in_place' script reference -- was invalid at this point
- refactor elasticsearch/opensearch integration
- make wildcard.hps integration explicit
- remove old upgrade steps for castle.cms 2.x (upgrade to latest 2.x version, then upgrade to 3.x version)
- remove custom elasticsearch index name (use wildcard.hps for customizing prefix, etc)
- change crawler to use wildcard.hps and optimize some queries
- remove infinite loop from crawler -- rely on system cron to actually perform loop behavior
- make crawler usable in an RO-Client context (as long as it has access to writable redis)
- use python argparse for crawler arguments
- initial update to .travis.cfg

Update note(s):

- After upgrading to 3.0.0b110, you will still have several ES related registry settings in your site that were not removed.
  This is to be non-destructive to configuration that you may want to reference, and to facilitate easier rollbacks if you must rollback for some reason.
  If they are no longer necessary, you can manually remove registry values related to `castle.cms.interfaces.IElasticSearchSettings`,
  Also, `castle.es_index` and `castle.es_index_enabled`.
  Leaving them will not affect the performance or operation of your site, however.


3.0.0b19 (2022-05-06)
---------------------

- fix dates while importing
- fix querylisting as folder view results bug


3.0.0b18 (2022-04-27)
---------------------

- handle error case in es_custom_index patch


3.0.0b17 (2022-04-20)
---------------------

- Allow unrestricted traverse to be selected when creating a pdf.


3.0.0b16 (2022-03-30)
---------------------

- Added some gallery options that will be used in some other add-ons.


3.0.0b15 (2022-03-04)
---------------------

- handle missing links in sticky footer


3.0.0b14 (2022-03-03)
---------------------

- pin plone.app.contenttypes and Products.ATContentTypes to versions that mitigate CVE-2022-25399
- fix template issue with sticky footer


3.0.0b13 (2021-12-02)
---------------------

- Fix paging display for many items in Content Browser component


3.0.0b12 (2021-11-29)
---------------------

- Reapply PR510 - icon and favicon downloads without changing functionality for other files
- slight refactor to be able to import slider config other places


3.0.0b11 (2021-09-17)
---------------------

- revert changes to Download class from PR#510
- bump plone.namedfile to 3.0.11


3.0.0b10 (2021-09-08)
---------------------

- enable tinymce for richtext widget on collective.easyform forms on anonymous form
- bugfix for site-icon 500 error under certain circumstances


3.0.0b9 (2021-09-01)
--------------------

- add height property to gallery tile schema


3.0.0b8 (2021-08-05)
--------------------

- fix edge case for folder_contents customization that causes pat-structure not to load properly


3.0.0b7 (2021-07-05)
--------------------

- fix upgrade step reference


3.0.0b6 (2021-07-05)
--------------------

- fix upgrade step version


3.0.0b5 (2021-07-05)
--------------------

- add initial implementation of a content type that supports parallax rendering


3.0.0b4 (2021-06-10)
--------------------

- recompile styles


3.0.0b3 (2021-06-08)
--------------------

- fix 2633 upgrade by adding metadata to action, and set default profile to 2633


3.0.0b2 (2021-06-01)
--------------------

- add ability to create templates from existing contents. templates are
  unpublishable and are managed as specially marked documents in a
  'template-repository' folder.


3.0.0b1 (2021-05-03)
--------------------

- add ES host/port override to reindex-catalog script
- add optional ES index creation to reindex-catalog script


3.0.0b0 (2021-04-30)
--------------------

BREAKING
++++++++

The 3.x series of releases will bring CastleCMS into compatibility with
ElasticSearch 7. Practically, this means primarily updating 3 packages:

* castle.cms >= 3
* collective.elasticsearch >= 4
* elasticsearch >= 7, <= 7.6

The `elasticsearch` package is restricted between 7 and 7.6 primarily due to
the restriction from `collective.elasticsearch` -- this is expected to be
updated at some point, but not for the initial release of `castle.cms` 3.x.

For migration, it is recommended that you setup a new ES cluster, update
site configurations to point at the new cluster, then do the "Convert" and
"Rebuild" actions in the ElasticSearch control panel.

This will not migrate your audit log, if enabled. To migrate the audit log,
use the `castle/cms/_scripts/export-audit-log.py` script to dump the old
audit log into a CSV file, and then use the `castle/cms/_scripts/import-audit-log.py`
script to import the CSV file into the new cluster.


2.6.31 (2021-04-20)
-------------------

- bugfix for custom index names for audit log


2.6.30 (2021-04-02)
-------------------

- changed default slideshow view to be the actual slideshow
  (Castle/some-slideshow now renders the view from Castle/some-slideshow/view-slideshow
  instead of from Castle/some-slideshow/view) (#482)
- changeNote bugfix (#483)
- auditlog use of customizable ES index name (#484 and #485)
- normalize folder contents column headings (#486)
- all-contents view for folder contents view (#487)
- update cryptography to 3.3.2 and update cffi to 1.14.5 (#461)


2.6.29 (2021-02-23)
-------------------

- fix labeling for required versioning behavior


2.6.28 (2021-02-23)
-------------------

- add custom IVersionable behavior to integrate better with audit log


2.6.27 (2021-02-15)
-------------------

- Separated backend and frontend configurations for robot instructions in html meta tags
- Added Current Castle Version to control panel Version Overview
- tweak audit log styling to help prevent overlap on normal sized screens
- add ability to customize default font sizing for tiles per object


2.6.26 (2020-12-22)
-------------------

- fix cloudflare cache purge unicode issue


2.6.25 (2020-11-10)
-------------------

- audit index name based on configured es index
- minor english grammar fixes
- custom markup field behavior for images,used in slider tile


2.6.24 (2020-11-02)
-------------------

- show warning instead of error if folder containing recycling is copied
- reset secure flow state and retry before 403
- disable autocaps for mobile logins


2.6.23 (2020-09-15)
-------------------

- exclude_from_search and has_private_parents features for public results
- panels to list items excluded from search for admin


2.6.22 (2020-09-10)
-------------------

- slideshow refinements
- add property per content item to exclude from search query
- query filter updates, including new wording and broader search


2.6.21 (2020-07-30)
-------------------

- fix the QueryListingTile to split display_fields correctly when passed as
  a query parameter to the @@castle.cms.querylisting view
- fix s3 integration in the edit/delete actions of the archival management view


2.6.20 (2020-07-14)
-------------------

- slideshow refinements


2.6.19 (2020-07-14)
-------------------

- slideshow refinements


2.6.18 (2020-07-14)
-------------------

- slideshow refinements


2.6.17 (2020-07-09)
-------------------

- revert manage-archives js and improve manage-archives usage of boto3 library


2.6.16 (2020-07-07)
-------------------

- slideshow upgrades and fixes
- fix password reset link in registration email
- improve scrub login at backend functionality


2.6.15 (2020-07-01)
-------------------

- update archival-manage view to deal with a large list of objects in an s3 bucket
  in a very basic, but functional (for now) way.


2.6.14 (2020-07-01)
-------------------

- fix js inclusion an archival-review view, move it to a resource definition


2.6.13 (2020-06-22)
-------------------

- js fix

2.6.12 (2020-06-22)
-------------------

- slideshow and search updates
  [bduncan137]
- some import/export work
  [daxxog]


2.6.11 (2020-06-04)
-------------------

- utilize resource registry instead of metal:javascript in some places
  [daxxog]
- add advanced player with no image
  [Takiyo]
- Slideshow enhancements and configuration options
  [bduncan137]


2.6.10 (2020-05-20)
-------------------

- ensure tag-manager js is run at the correct time


2.6.9 (2020-05-11)
------------------

- try and ensure that search.js is loaded after everything else is loaded on the page.


2.6.8 (2020-04-30)
------------------

- update archival/aws links
- stop excessive logging about tile lockinfo


2.6.7 (2020-04-21)
------------------

- Fix broken links for youtube video
- Add Ability to select custom itunes image per syndication folder
- Don't error on missing fragment used, rendering warning

2.6.6 (2020-04-13)
------------------

- Sticky footer updates
- Secure login updates


2.6.5 (2020-03-27)
------------------

- Don't show overview page without host header.
  [lucid-0]
- Pass on private_parents check when brain not found
  [lucid-0]

2.6.4 (2020-03-26)
------------------

- go to zope root rather than dashboard for root logins coming from logged_out
  [lucid-0]


2.6.3 (2020-03-25)
------------------

- allow people logging in at zope root to go straight to /manage
  [lucid-0]


2.6.2 (2020-03-25)
------------------

- Remove Audio type from metadata stripping on upload (exiftool does not support)
  [lucid-0]
- Add security panel option to allow access to published content inside a private container
  (this behavior used to be default, now defaults to false but option requested)
  [lucid-0]
- Add empty-trash log to site annotations, and to the @@trash view
  Users can see which, and how many items were removed by the script.
  [lucid-0]
- Add audit logging for changes to configuration registry, theme selection,
  and manual trash emptying.
  [OdiumSpeck]
- Updates to audio tile schema and template, advanced player in castle.advantage
  [Takiyo]

2.6.1 (2020-03-02)
------------------

- secure-login fixes, test updates
  [lucid-0]


2.6.0 (2020-02-27)
------------------

- a couple sticky footer tweaks and static build
  [lucid-0, OdiumSpeck]


2.5.19 (2020-02-20)
-------------------

- Building static and fixing profile
  [lucid-0]


2.5.18 (2020-02-20)
-------------------

- add initial slideshow support
  [lucid-0]

- change pdf metadata removal to be more particular so that form fillable pdfs will still be usable
  [alphaomega325]

- move adapter override to override.zcml
  [zombified]

- fix for history version template to correctly check for associated image
  [zombified]


2.5.17 (2020-02-17)
-------------------

- add preliminary support for category subscriber emails to be used in content rules
  [zombified]

- upgrade to boto3 library
  [zombified]

- add first visit / disclaimer message options
  [cmher]

- move authentication flow to backend
  [lucid-0]

- fix news item tiles without names, catch querylisting url error
  [alphaomega325]

- improve loading and error message for google analytics
  [lucid-0]

- add index and logic to hide published items contained in private folders
  [lucid-0]


2.5.16 (2019-10-07)
-------------------

- Fix upgrade step
  [lucid-0]

2.5.15 (2019-10-07)
-------------------

- add sticky footer tile
  [lucid-0]

- integrate Google Tag Manager
  [lucid-0]

- Redirect to /@@secure-login if it's in request path
  [lucid-0]

- Serve strict robots.txt to backend URL
  [lucid-0, Chue Her]

2.5.14 (2019-07-18)
-------------------

- fix search.js for ie 10/11


2.5.13 (2019-06-27)
-------------------

- fix og:image tag duplication issue


2.5.12 (2019-05-28)
-------------------

- unicode fix


2.5.11 (2019-05-21)
-------------------

- Update pdf reprocess script
  [lucid-0]

- Show field descriptions to anon again
  [lucid-0]


2.5.10 (2019-05-14)
-------------------

- Improve PDF Metadata stripping


2.5.9 (2019-05-07)
------------------

- Be able to provide oauth providers for `@@secure-login`
  [vangheem]

- Add Audio Transcript to file template
  [lucid-0]

- Survey Invite optional logo, styling update
  [lucid-0]

- Fix RichText import when exporting from old Plone
  [lucid-0]


2.5.8 (2019-03-29)
------------------

- Add site title to social meta tags
  [lucid-0]


2.5.7 (2019-03-28)
------------------

- use registry values in itunes feed
  [lucid-0]


2.5.6 (2019-03-26)
------------------

- Some nudges for the tooltip alignment
  [RobZoneNet]

- Do not delay on quality check
  [vangheem]

- Fix quality check closing error box after load
  [vangheem]


2.5.5 (2019-03-25)
------------------

- Add missing upgrade step
  [vangheem,RobZoneNet]

- Add blank coverimage.pt fragment so we don't get errors on
  themes that don't implement it
  [RobZoneNet]


2.5.4 (2019-03-25)
------------------

- Handle ES error when getting search options
  [vangheem]

- Provide date search options
  [vangheem]

- Make the secure login accessible
  [RobZoneNet]

- Add in tooltips for the main toolbars
  [RobZoneNet]



2.5.3 (2019-03-08)
------------------

New:

- Be able to specify robots meta tag configuration for content
  [vangheem]

- Add `distribution=Global` meta tag
  [vangheem]


Changes:

- Show published date in search results
  [vangheem]

- Show transcript in video view
  [lucid-0]


Fixes:

- Run exiftool on Audio and Video types as well
  [vangheem]

- Fix redirect url for logging into site
  [vangheem]

- Remove duplicate description head metadata tag
  [vangheem]

- Remove duplicate keywords head metadata tag
  [vangheem]


2.5.2 (2019-03-01)
------------------

Fixes:

- enable quality check delay
  [lucid-0]


2.5.1 (2019-02-27)
------------------

Fixes:

- Implement IAnnotations for IResourceDirectory to prevent errors
  previewing theme through the editor.
  [vangheem]

- Fixed Querylisting so the title is required since it is a h2. This is good for accessibility. I also put a classname in the h2 tag so the end themer can hide from visual but not screen readers
  [RobZoneNet]

- Added video icon and event hover icon for the add modal
  [robzonenet]

- Bug fix to UploadNamedFileWidget
  [vangheem]


2.5.0 (2019-02-15)
------------------

New:

- Integrate uploading to youtube
  [lucid-0,vangheem]

- Add `link-report` script and `Broken links` control panel
  [vangheem]

- Be able to configure some default settings with environment variables
  [vangheem]

Fixes:

- Fix cache invalidation with jbot on production
  [vangheem]


2.4.1 (2019-02-06)
------------------

- Fix bugs with getting site icon
  [vangheem]

- Fix adding Query Choice easyform field
  [vangheem]


2.4.0 (2019-01-28)
------------------

New:

- Implement being able to add tiles from inside your theme folder
  [vangheem]

- Implement new `Query Choice` field for collective.easyform which
  allows you to specify a query to retrieve values from. In order to use,
  you need to activate the field in the Easy Form Control panel.
  [vangheem]

- Add `--skip-incomplete` option to `upgrade-sites` script to bypass
  erroring when an profile does not upgrade corrrectly
  [vangheem]

Changes:

- use `summary_large_image` twitter card instead of `summary`
  [vangheem]

- Better PDF generation error handling and logging
  [vangheem]

- Reorganize `castle.cms.utils` module so split into sub-modules. Imports
  are all still same.
  [vangheem]

Fixes:

- Fix duplicate `<head>` tags showing up
  [vangheem]

- Fix jbot theme customizations bleeding across sites
  [vangheem]

- Upgrade mosaic to fix layout selection styles
  [vangheem]

- Handle errors in resolving menu items
  [vangheem]

- Provide patch for https://github.com/celery/celery/pull/4839 until
  it is fixed in a release
  [vangheem]

- Skip auto-upgrading `collective.easyform` in `upgrade-sites` script
  because it does not correctly define upgrade steps
  [vangheem]

- Handle errors caused by urls like `pdf/download` which should just
  be a 404.
  [vangheem]


2.3.8 (2019-01-15)
------------------

New:

- import fixes: transition item only if it needs it; loop over all workflow
  chains (usually there is only one); set the workflow history (do not add
  extraneous entries caused by the import process)
  [tkimnguyen]

- export-content.py now takes --modifiedsince and --createdsince args
  e.g. --modifiedsince='2018-10-03 00:00:00'
  [tkimnguyen]

- Be able to run castle upgrades directly from addon control panel
  [vangheem]

- Provide new `upgrade-sites` script to automatically run plone/addon
  upgrades for all sites in an instance
  [vangheem]

- Add contentlisting summary view which repeats the container image
  and displays publication date.
  [lucid-0]

Fixes:

- Upgrade collective.documentviewer == 5.0.4
  [vangheem]

- Handle scaling errors on favicon view
  [vangheem]

- Handle errors on non-folderish dexterity items feed setting lookups
  [vangheem]

- Handle unicode issues with querylisting tile and ES
  [vangheem]

- Handle potential IOError and POSKeyError on serving files to give 404 now
  [vangheem]

- Fix crawler memory error by streaming crawler requests(don't load non-html content)
  [lucid-0]

Changes:

- Reorganize `castle.cms.browser` module and add robot framework tests
  [vangheem]


2.3.7 (2019-01-02)
------------------

New:

- Add session timeout configuration to Security panel
  [lucid-0]

- Add audio/video twitter cards
  [vangheem, lucid-0]


Fixes:

- Handle error in `@@content-body` when there is no IFeedItem adapter
  for the current context
  [vangheem]

- Fix twitter cards
  [vangheem, lucid-0]

Changes:

- Registered utility for site content importer to allow add-ons to
  create content types for importing
  [obct537]


2.3.6 (2018-12-20)
------------------

Fixes:

- Upgrade collective.elasticsearch to fix sorting issues and negative
  indexing implementation
  [vangheem]

Changes:

- Default to reversed sorting and explicitly use effective date sorting
  for query listing tile.


2.3.5 (2018-12-17)
------------------

New:

- Add request interval option to crawler
  [lucid-0]


Fixes:

- Upgrade collective.elasticsearch to 2.0.4 to fix date
  queries that use `min:max`
  [vangheem]

- Fix querylisting not filtering by tags anymore
  [vangheem]

- fix popup modal close button to be visible on mobile
  [vangheem]

- Upgrade plone.app.mosaic to fix protect.js script tag being
  loaded over and over again in edit mode
  [vangheem]

- Fix alias causing logout at backend urls
  [lucid-0]

- Upgrade collective.celery
  [vangheem]

- Fix: Use ArchiveManager to getContentToArchive
  [lucid-0]


2.3.4 (2018-12-10)
------------------

- Fix upgrade of `castle.slot_tiles` when it's been set to None
  [vangheem]


2.3.3 (2018-12-10)
------------------

New:

- Implement new modal link
  [vangheem]

- Add import subscribers form for announcements panel
  [CorySanin]

- Add new recurrences indexer
  [tkimnguyen]

- Calendar tile now renders recurring events
  [obct537]

Fixes:

- Handle error when image tile referenced image is not found
  [vangheem]

- Fix use of celery with always eager setting and some tasks
  [vangheem]

- Work with ffmpeg as well as avconv
  [vangheem]

- Make content listing tile persistent. This fixes issues with saving
  data to content listing tile.
  [vangheem]


2.3.2 (2018-12-04)
------------------

Fixes:

- Fix reindexing causing `last_modified_by` index to get overwritten
  [lucid-0,vangheem]

- Fix 2.0.41 upgrade step that cleared `slot_tiles` setting and
  attempt to fix missing `slot_tiles` on sites that have been
  upgraded since.
  [vangheem]


2.3.1 (2018-12-04)
------------------

New:

- Upgrade to latest collective.elasticsearch.
  New versions include,
  `collective.celery=1.1.2`,
  `collective.elasticsearch=2.0.2`,
  `celery=4.2.1`,
  `billiard = 3.5.0.4`,
  `kombu = 4.2.1`,
  `redis = 2.10.5`

Fixes:

- Fix z-index issue with recurrence modal for events
  [robzonenet]

- Fix import Folder to not customize layout when text is empty
  [vangheem]

- Fixed broken update step
  [obct537]


2.3.0 (2018-11-27)
------------------

New:

- Add Mamoto support (CastleCMS API control panel settings, Twitter & Facebook share counting and Analytics display);
  remove EOL'd Facebook and LinkedIn API social counts
  [tkimnguyen]

Fixes:

- Fixed registry upgrade blanking out the plone.backend_url recored
  [obct537]

- Do not error when upgrade hasn't been run for only allow backend urls
  [vangheem]

- Handle incorrectly configured backend url/sheild settings
  [vangheem]


2.2.2 (2018-11-26)
------------------

- fix mosaic build js/css


2.2.1 (2018-11-21)
------------------

- Upgrade CMFPlone to fix meta bundle ordering
  [vangheem]

- Do not redirect to `/not-found`, just directly render not found template
  [vangheem]

- Adding basic Robot testing setup
  [obct537]

- Make recaptcha work with embeddable content tiles
  [lucid-0]

- Since the carousel is behind aria-hidden, the whole thing is wisely skipped by screen readers. But still it is a requirement to not leave anchor tags empty  https://www.w3.org/TR/UNDERSTANDING-WCAG20/navigation-mechanisms-refs.html see 2.4.4 and https://www.w3.org/TR/2016/NOTE-WCAG20-TECHS-20161007/G91.
  [RobZoneNet]

2.2.0 (2018-11-15)
------------------

- Accessibility colorblindness changes for editing buttons. The default bootstrap colors are mostly not accessible.  Changed colors for things like notifications numbers, information messages, and some other buttons.
  [RobZoneNet]

- Handle potentially weird ConnectionStateError on login
  [vangheem]

- Be able to customize file upload fields
  [vangheem]

- Show form errors in the mosaic interface so user knows if there
  are required fields missing or errors in fields
  [vangheem]

- Fixed the ability to click on "Add News Item" and getting the expected add news item modal.
  [RobZoneNet]

- Fixes for folder_contents page. The query box layout and how it reacts to different widths
  of a browser. Fixed the top tool bars as well for narrow browsers. Fixed colors for
  dashboard search button due to failing colorblindness tests
  [RobZoneNet]

- Clarified the add -- upload modal
  [RobZoneNet]

- do not attempt to publish item is already published content with `@@publish-content` view.
  [vangheem]

- Add "Manage Categories" tab to announcements control panel
  [CorySanin]

- Upgrade mockup to fix dev mode on contents page
  [vangheem]

- Rename some Castle -> CastleCMS titles and labels
  [tkimnguyen]

- Fix potential querylisting unicode errors from form input
  [vangheem]

- Fix the layout of the theming control panel buttons
  [RobZoneNet]

- Fix accessibility issue with the querylisting templates injecting empty A tags
  [RobZoneNet]

- Fix saving default values for Dexterity fields
  [CorySanin]

- Handle potential errors caused by invalid references in folder ordering.
  See https://github.com/plone/plone.folder/pull/10 for details
  [vangheem]

- Fix resources references which was causing a bunch of 404 errors
  [vangheem]

- Add Keyword Manager (Products.PloneKeywordManager) by default
  [CorySanin]

- Remove _permissions DeprecationWarnings from startup
  [CorySanin]

- Fix change password on login
  [CorySanin]

- Various import/export fixes
  [vangheem]

- Allow trailing slashes in backend URLs
  [CorySanin]

- Use chunked upload on edit forms with NamedFile fields
  [lucid-0]

- Allow custom FROM for announcement emails
  [lucid-0]


2.1.1 (2018-10-02)
------------------

- Fix password reset function
  [CorySanin]

- Fix not Schema AttributeError on export script
  [vangheem]

- Add support for the path search parameter
  [CorySanin]

- Update twitter embedding code and templates
  [lucid-0]

2.1.0 (2018-09-26)
------------------

- Add support for the Subject:list search parameter
  [CorySanin]

- Add password expiration option with whitelist
  [CorySanin]

- Fixed a bug with the tab order on the login screen
  [CorySanin]

- The button for creating a custom content type now defaults to cloning an existing one
  [CorySanin]

- Hide field descriptions when not logged in
  [CorySanin]

- Hide the Edit XML button from the Dexterity fields page unless "advanced mode" is enabled
  [CorySanin]

- add info and warnings for missing REDIS_SERVER env var
  [tkimnguyen]

- add copyright year to footer of new sites at create time
  [tkimnguyen]

- handle Celery connection errors in Tasks control panel
  [tkimnguyen]

- Rearranged image tile settings, clarified terminology
  [CorySanin]

- import script fixes
  [tkimnguyen]

- Use the image_url property for file_url when file is an image
  [lucid-0]

- disallow logins from non-backend URLs, if set in Security panel; tweaks to field descriptions
  [CorySanin]

- improve export and import scripts
  [tkimnguyen]

- tweak find-broken-links.py script
  [tkimnguyen]

- Changed collective.documentviewer dep. version
  [obct537]

- Added status control panel to give users the status of relevant subprocesses
  [mattjhess]

- in query listing tile, do not display event start/end if they don't exist
  [tkimnguyen]


2.0.45 (2018-07-13)
-------------------

- add Event start and end datetimes to the query listing tile's views
  [tkimnguyen]

- add Site Crawler control panel field descriptions
  [tkimnguyen]

- check for when Twitter-related keys in twitter-monitor
  [CorySanin]

- Added Beautifymarkers leaflet extension, adds map icon customization
  [obct537]

- add celery environment vars for connecting to redis
  [tkimnguyen]

- Added fragments directory ZCML directive
  [obct537]

- Add Survey invite tile and controlpanel
  [lucid-0]

- Replace deprecated 'mockup-patterns-base' with 'pat-base' in several files
  [lucid-0]

2.0.44 (2018-05-08)
-------------------

- fix default news item layout
  [tkimnguyen]

- add description to Etherpad fields
  [tkimnguyen]

2.0.43 (2018-04-06)
-------------------

- Add simple display type to existing content tile (displays body of article)
  [lucid-0]

- show relative and absolute datetimes in contents view
  [robzonenet]

- change default site announcement text
  [tkimnguyen]

- Change email category widget. Make subscribe title editable. Updated to work with Plone 5.0.x
  [lucid-0]

2.0.42 (2018-03-01)
-------------------

- tweak tour text
  [tkimnguyen]

- fix CastleCMS spelling
  [tkimnguyen]

- tweak installation instructions
  [tkimnguyen]

- add version pins
  [tkimnguyen]

- remove duplicate location of site announcement settings
  [tkimnguyen]

- correct typos; add descriptions to control panels
  [tkimnguyen]

- improve URL shared via sharing buttons
  [tkimnguyen]

2.0.41 (2017-09-26)
-------------------

- print.css improvements
  [robzonenet]

2.0.40 (2017-09-26)
-------------------

- accessibility and print.css improvements
    [robzonenet]

2.0.39 (2017-09-20)
-------------------

- 2-level nav improvements for mobile
  [robzonenet]

2.0.38 (2017-09-18)
-------------------

- Fixed the missing print stylesheet
    [robzonenet]


2.0.36 (2017-08-01)
-------------------

- Fixed issue breaking the history view on content
  [obct537]


2.0.35 (2017-07-26)
-------------------

- Added in a 2 level navigation
  [robzonenet]


2.0.34 (2017-07-03)
-------------------
- Changed map attribution string to include OpenStreepMap
  [obct537]

- Fixed problem breaking content history view
  [obct537]

- add new CastleCMS pypi classifiers
  [lucid-0]

- Added a toolbar button to allow users to manually mark an object for archiving
  [obct537]

2.0.33 (2017-05-8)
-------------------

- Site install now wont add duplicate slot tiles
  [obct537]

- Original image scale now actually does something
  [obct537]


2.0.32 (2017-04-28)
-------------------

- Better error pages with stacktrace info if it's possible to provide
  [vangheem]

- Be able to modify comments made on a historic content object history data
  [vangheem]

- Fix 404 not being protected by login shield.
  [vangheem]

- After login should now redirect you to `/@@dashboard` or to the original
  url you requested if you were redirected to login page
  [vangheem]

- Updated defaults for the image tile
  [obct537]


2.0.31 (2017-04-18)
-------------------

- Fix version pin for plone.app.content to work correctly with folder contents
  and changing date properties
  [vangheem]

- Build css/js with latest mockup but disable now/clear buttons on pickadate
  so they are unstyled and look bad with castle.
  [vangheem]

- Fix password reset template to send user's username instead of id
  [vangheem]

- export-content.py now works to export dexterity and mosaic pages
  [vangheem]

- fix crawling gz sitemaps
  [vangheem]

- Resolved issue where the the words 'site settings' showed up when clicked
  [robzonenet]

2.0.30 (2017-04-12)
-------------------

- Fix create user to send out correct password reset url
  [vangheem]

- Handle issue getting current user when logging in. Can happen with authomatic
  [vangheem]

- fix cases where generated absolute url was incorrect based on the original
  result html not being used for the base path
  [vangheem]

- Resolved issue where invalid sort parameters broke the querystring tile. Closes issue #42
  [obct537]

- Resolved issue where the images were missing due to the url being wrong. Closes issue #17
  [robzonenet]



2.0.29 (2017-04-04)
-------------------

- Change "Read transcript" link to "Transcript | Download"
  [vangheem]
- Fix issue where a span tag was being added to the castle toolbar which is an accessibility issue.
  [robzonenet]
- Fix accessibility issue of not having words in the cog button. The screen reader needs to read something.
  [robzonenet]


2.0.28 (2017-03-28)
-------------------

- Use ssl for maps data urls
  [vangheem]


2.0.27 (2017-03-27)
-------------------

- Fix issue where archetypes content in castle.cms would cause potentially
  inconsistent search results.
  [vangheem]


2.0.26 (2017-03-27)
-------------------

- Fix potential issue with upgrading to latest version of collective.elasticsearch
  [vangheem]


2.0.25 (2017-03-27)
-------------------

- Fix regression from login fix
  [vangheem]


2.0.24 (2017-03-27)
-------------------

- Do not require selection of images for gallery/slider tile so that query
  field will work
  [vangheem]


2.0.24 (2017-03-27)
-------------------

- Fix cron scripts to look in more locations for zope.conf
  [vangheem]


2.0.23 (2017-03-27)
-------------------

- Be able to provide dynamic query for gallery and slider tiles
  [vangheem]

- Fix issue where feature tile was not mobile friendly
  [RobZoneNet]

- Provide link back to original image item from slider/gallery tiles
  [vangheem]


2.0.22 (2017-03-27)
-------------------

- Fix case where query results would not correctly get results when using the filter.
  [vangheem]


2.0.21 (2017-03-24)
-------------------

- Fix some cases where default plone workflow was assumed
  [vangheem]


2.0.20 (2017-03-24)
-------------------

- Be able to specify external url for the image tile.
  [vangheem]


2.0.19 (2017-03-23)
-------------------

- Fix case where default page would not be imported correctly on some sites. By
  default import will always attempt to treat a lead image for folder content.
  [vangheem]


2.0.18 (2017-03-22)
-------------------

- Make AtD support work with mosaic rich text tiles
  [vangheem]

- Integrate AtD with quality check. If active, quality check will also notify
  potential spelling/grammar issues.
  [vangheem]


2.0.17 (2017-03-22)
-------------------

- Fix issue where empty lead images would get imported from old lead image package
  and no filename would be found.
  [vangheem]


2.0.16 (2017-03-21)
-------------------

- Fix event type to have lead image and search customization
  [vangheem]

- Fix import of event type
  [vangheem]


2.0.15 (2017-03-21)
-------------------

- Fix OFS missing import in importtypes
  [vangheem]

- JSON feed now works with body option
  [obct537]


2.0.14 (2017-03-20)
-------------------

- Provide information on lead image when inspecting history
  [vangheem]

- Handle zeoserver errors for syndication
  [vangheem]


2.0.13 (2017-03-20)
-------------------

- Fix invalid date issue from crawled pages on search results page
  [vangheem]

- auto detect lead images from content in the layout
  [vangheem]


2.0.12 (2017-03-15)
-------------------

- Fix paste button not working and throwing unauthorized errors because of
  missing csrf token. Fixes #19
  [vangheem]

- Automatically detect image in content if no lead image is set. Fixes #28
  [vangheem]

- Fix showing non-image content on lead image browse selector. Fixes #30
  [vangheem]

- Be able to provide additional views for the existing content tile
  [vangheem]

- Be able to specify upload location
  [vangheem]


2.0.11 (2017-03-09)
-------------------

- Fix image focus point upgrade issue where it would request more images than
  it should
  [vangheem]

- Provide image_url for json feed
  [vangheem]

- If commenting enabled on a folder, it will become the default for all children
  in that folder.
  [vangheem]


2.0.10 (2017-02-06)
-------------------

- Fix next/prev nav fragment to work with pages and site root
  [vangheem]

- Fix fullcalendar issue with selecting text when one is dropped on page.
  This requires building with mockup on fix-jquery-event-drag-compat branch
  or master once it's merged
  [vangheem]

- Override default Zope2 logging to log actual plone username in Z2.log
  [vangheem]


2.0.9 (2017-01-23)
------------------

- Add automatic session refresh support
  [vangheem]


2.0.8 (2017-01-21)
------------------

- Be able to provide your own google maps api key so that working with the
  mapping widget works more consistently.
  [vangheem]

- Use argon2 pw encryption scheme by default
  [vangheem]


2.0.7 (2017-01-18)
------------------

- Fix previous release


2.0.6 (2017-01-18)
------------------

- Fix logged in event not recorder in the audit log correctly
  [vangheem]


2.0.5 (2017-01-18)
------------------

New:

- Add new JSON feed type
  [vangheem]

Fixes:

- Fix parsing querylisting selected-year query
  [vangheem]

- Fix parsing querylisting Title/SearchableText query
  [vangheem]

2.0.4 (2017-01-09)
------------------

- add rocket chat integration
  [sam schwartz]

- fix issue where password reset wasn't sticking
  [vangheem]

- make sure logout page shows login form
  [vangheem]

- add clean-drafts script
  [vangheem]

- add ping draft view so that the clean-drafts script knows not to clean a potentially
  active draft
  [vangheem]

2.0.3 (2016-12-20)
------------------

- Be able to pass in a site object to the render_content_core function for
  layout aware items
  [vangheem]


2.0.2 (2016-12-14)
------------------

- build resources
  [vangheem]

2.0.1 (2016-12-14)
------------------

- fix ipod/ipad safari video background image issue
  [robzonenet]


2.0.0 (2016-12-07)
------------------

- Initial public release
