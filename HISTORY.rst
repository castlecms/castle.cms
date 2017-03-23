Changelog
=========

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
