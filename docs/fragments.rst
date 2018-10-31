Fragments
=========

Fragment description here...

Fragment Directories
--------------------

To include new fragments into a CastleCMS site using a non-theme add-on,
throw them in a folder, and add a declaration to your `configure.zcml`:

Folder structure:

* my.package
    * configure.zcml
    * fragments
        * fragment1.pt
        * fragment2.pt

configure.zcml:

.. code-block:: xml

    <fragmentsDirectory
      name="my.package.fragments"
      directory="fragments"/>

The `name` field is largely unimportant, but needs to be unique. The
`directory` value is a relative path to folder containing your fragment
.pt files.
