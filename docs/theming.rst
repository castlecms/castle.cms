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


Tiles
-----

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
