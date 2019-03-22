Upgrading to CastleCMS 3
========================

CastleCMS 3.x introduces Python 3/Plone 5.2 support.


Recommended way...
------------------

- copy zodb to environment with py 2.7 + castle.cms 3.x
- migrate zodb
- move to py 3 env


References
----------

- https://zope.readthedocs.io/en/latest/ZODB-migration.html


Where things might break
------------------------

- Python scripts stored in ZODB that are not Python 3 compat
- The above also applies to page templates with embedded py code