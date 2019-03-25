Upgrading to CastleCMS 3
========================

CastleCMS 3.x introduces Python 3/Plone 5.2 support.


References
----------

Read this before you start!!!

- https://zope.readthedocs.io/en/latest/ZODB-migration.html


Recommended steps...
--------------------

- copy zodb to environment with py 2.7 + castle.cms 3.x
- go to each site and run upgrade... `@@plone-upgrade`
- run: `bin/zodb-py3migrate-analyze path/to/Data.fs -b path/to/blobstorage`
- run: `bin/zodbupdate --pack --convert-py3 --file path/to/Data.fs`
- copy/paste the zodb/blobstorage to new env with py 3/castle cms 3
- run server
- go to /manage -> portal_setup
    - delete all indexes
    - delete all metadata



Where things might break
------------------------

- Python scripts stored in ZODB that are not Python 3 compat
    - needs to be fixed ahead of time!!!
- The above also applies to page templates with embedded py code