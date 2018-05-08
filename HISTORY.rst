
Changelog
=========

2.0.45 (unreleased)
-------------------

- Nothing changed yet.


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
