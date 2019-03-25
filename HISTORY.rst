Changelog
=========

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
