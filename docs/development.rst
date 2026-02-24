Development
===========


Compiling resources after changes to js or less
-----------------------------------------------

Just regular plone compile resources::

    ./bin/plone-compile-resources --site-id=Castle --bundle=plone
    ./bin/plone-compile-resources --site-id=Castle --bundle=plone-logged-in

Running this command runs npm install from /castle.cms/package.json, and generates a Gruntfile.js
in /castle.cms. Once this has been run, however, for ongoing development of .less files or .js files,
there is no need to run npm install or generate the Gruntfile again, so there are additional faster commands
that can be run for compiling. Many of the useful ones can be found in /castle.cms/Makefile. For instance,

   make less-plone-logged-in

will only deal with the less files and leave everything else alone. If for some reason, more fine-grained
control is desired, or compilation is needed on some less-commonly-worked with bundles, look at the registered tasks
at the bottom of the generated Gruntfile.js for inspiration.


When updating bundles (most commpnly plone or plone-logged-in), an upgrade step will be required in which the
`last_compilation` key is updated in registry/resources.xml. Without this, those compiled changes will
not be reflected in the site.


Adding external toolbar buttons
-------------------------------

Unfortunately the Castle toolbar is a bit more complicated than the Plone alternative.
Because of the greatly increased reliance on JavaScript to create the behaviour of
the buttons/menus on the toolbar, creating a new button requires a few more steps.

The process will vary depending on how involved your new button is, but the steps will
resemble the following:

1) Using the install profile of your add-on, add an entry to the castle.toolbar_buttons
   registry entry. (see castle/cms/profiles/default/registry/castle.xml).
   This should be a link to a AMD-style React component. To save a lot of effort,
   inherit from the menu-item or modal-item modules in the static/patterns/toolbar folder.
   Make sure the component passed backs contains a 'name' variable, and a 'menu',
   (either 'side' or 'top') to the React props.

   The CastleCMS toolbar will then pull in this class after the initial page load, and
   attach the functionality to the appropriate button (created in the next step).

2) Add an entry in the actions.xml profile file, just like in Plone. However, if your button
   will be adding a modal functionality (not redirecting the browser to another page),
   omit the 'url_expr' value.


Testing upgrades
----------------

CastleCMS now has integration tests for upgrades between versions of CastleCMS.

To add additional tests between specific version tests, review the `test_upgrades.py`
file. Specifically, the variable `TEST_VERSIONS` provides the definition of what
tests will be run.

Also notable is the ability to set registry data for the installed site. This is
useful when running you have upgrades that modify the registry.
