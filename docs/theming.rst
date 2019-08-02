Theming
=======

Theming in Castle has some differences than with standard Plone. The most
notable difference is that Castle theming is *NOT* using diazo.

Diazo was a layer of indirectly and complexity that CastleCMS decided to
not take on. Additionally, the context of a completely tile-ified theming
approach, the need for diazo is dramatically reduced.


Themes
------

Themes are still registered and managed in the same exact way themes are
with regular Plone. You create a theme package or zip file, provide a
`manifest.cfg` file and boom, you have a castle theme.

The most notable difference is that the value for `rules =` is emptied
in a castle theme. This is what tells castle for forgo rendering the
theme as a castle theme and instead tells it to render as a regular
template with tiles.


Layouts
-------

Primarily, themes consist of a layout. The default layout is the `index.html`
file in your theme.

Any additional `.html` files in the root of the theme are available as selectable
layouts from the `Design` button on content. These can be applied to content
or an entire section of content.

Layout files in themselves are simply chameleon template files that render html. They
mostly consist of the html structure of your site along with tile placements
for where you want to render parts of your site.

Available variables:

- `site_url`: Current site base url
- `portal_url`: Alias of `site_url`
- `context_url`: Current context url
- `request`: Request object
- `context`: Current context object
- `site`: Site object
- `portal`: Alias of site object
- `theme_base_url`: Base url to theme
- `content`: dictionary of `{"left": ..., "right": ..., "main": ...}` to fill main content of site with
- `anonymous`: if current user is anon
- `debug`: if in debug mode
- `utils`: castle utilities reference

Important constructs:

- `<html data-gridsystem="...">`: define what time of grid system. Example `bs3`
- `<div data-tile="{context_url}/..." />`: render a tile
- `<link data-include-js />`: include configured site javascript
- `<link data-include-css />`: include configured site css
- `dynamic-grid`: dynamically expand empty grid columns


Layout tiles
------------

Tiles are the building block of everything in Castle. Tiles are what render most
of the content on the page and are also what are dynamically inserted onto a page
inside of content and with meta tiles.

Common layout tiles:

- `@@castle.cms.metadata`: current context metadata
- `@@plone.app.standardtiles.toolbar`: editing toolbar
- `@@fragment`: render registered fragment. Example: `${portal_url}/@@fragment?name=mainlinks`
- `@@castle.cms.meta/meta-[name]`: Meta tiles are froups of tiles like what
   are portlets in old-school Plone. You can add as many as you want.
   Example: `${context_url}/@@castle.cms.meta/meta-left`
- `@@plone.app.standardtiles.global_statusmessage`: render status messages
- `@@plone.app.standardtiles.lockinfo`: render lock info
- `@@plone.app.standardtiles.viewletmanager`: b/w compatible way to render viewlet
  manager directly. Example: `${context_url}/@@plone.app.standardtiles.viewletmanager/below-content?manager=plone.abovecontentbody`
- `@@plone.app.standardtiles.analytics`: render content analytics include code


Meta tiles(not portlets)
------------------------

Portlets were a useful construct to render groups of dynamic content in
various places in a site.

Meta tiles are essentially the same concept; however, they unified the usage
with tile rendering. This means that tiles are still the essential building
block for all content of a site and we don't have separate concepts/widgets/etc
for portlets.

Meta tiles can be placed anywhere in the theme and do not need any specific
registration or configuration.


Theme tiles
-----------

You can provide custom tiles in your theme as well.

To create a tile, you need 2 files: 1) a `config.json` and 2) a `template.html` file
to be placed inside a folder

`config.json` is used to define fields and configuration of the tile.

For example, add the file `tiles/mytile/config.json` with the following::

   {
      "title": "Foobar",
      "description": "A tile for foobar",
      "category": "advanced",
      "weight": 200,
      "fields": [{
         "name": "foobar",
         "title": "Foobar"
      }, {
         "name": "image",
         "title": "Image",
         "type": "image",
         "required": true
      }]
   }

WARNING: Your folder name is the "id" of the tile. If you change this,
you lose the reference of tile and data on the site. If you remove the folder,
existing tiles of the type will then display as empty.

Then, add your `tiles/mytile/template.html` file::

   <p>Hello World! ${data/foobar|nothing}</p>
   <div tal:define="image python: get_object(data.get('image'));">
      <img tal:condition="nocall: image|nothing" src="${image/absolute_url}/@@images/image/large" />
   </div>


Available configuration options:

- `title`: the title of the tile
- `description`: the description that will show up on the add form
- `category`: section of menu the tile will show up on. Options are:
  `structure`, `media`, `social`, `properties`, `advanced`.
  New categories will automatically create new menu section.
- `weight`: weight to be applied to the positioning of the tile in the menu
- `fields`: array of fields to have included on the add/edit form
- `hidden`: if you want to no longer show tile in menu


Available field options:

- `name`: field name used to uniquely identify the value
- `title`: title of the field
- `description`: description of the field
- `type`: field type(see below for available types)
- `default`: default value for the field
- `required`: if a value is required or not. Default to `true`


Available field types:

- `text`
- `int`
- `float`
- `decimal`
- `datetime`
- `date`
- `time`
- `password`
- `boolean`
- `choice`: must provide `"vocabulary": ["one", "two"]`
- `uri`
- `dottedname`
- `array`
- `image`: will store a reference to an image
- `images`: select multiple images
- `resource`: will store reference to content on site
- `resources`: select more than one content from site


Available template globals:

- `context`
- `request`
- `view`
- `data`: configured data for the tile
- `get_object`: function to get object from reference
- `utils`: castle utilities
- `portal_url`
- `public_url`
- `site_url`
- `registry`
- `portal`

NOTE: when making changes to tile configuration in production, you need
to clear the theme cache in order for the new changes to take affect.
