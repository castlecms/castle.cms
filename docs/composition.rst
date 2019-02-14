Composition
===========

All content in Castle CMS is a "content type" like `Page`, `News Item`, `Image`,
`Video`, etc.

The composition of each of those items and how the page is assembled and presented
to users is done with smaller individual components called "tiles".

Many tiles compose the content of a single page. Almost everything in CastleCMS is a tile.


Tile display types
------------------

There are tiles provided by CastleCMS that allow you to customize
the display type. The display type field is a way of providing a different
view of the content.

Available display type tiles include the following (along with the matching display type vocabulary ID):

 - Navigation (navigation)
 - Existing content (existing)
 - Gallery (gallery)
 - Query Listing (querylisting)


Providing your own display types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are 3 components to registering a display type for a tile:
  - Display type class
  - Page template
  - ZCML registration


Example custom display type
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is an example of creating a custom display type for the existing content tile.

Define the display type class::

    class MyTileView(BaseTileView):
        name = 'myview'
        preview = '++plone++castle/path/to/image.png'
        order = 1
        index = ViewPageTemplateFile('myview.pt')
        tile_name = 'existing'


Then define the template::

    <tal:wrap tal:define="utils view/tile/utils;
                          data view/tile/data;
                          df view/tile/display_fields;
                          idt data/image_display_type|string:landscape;
                          existing nocall: view/tile/content|nothing;
                          url python: utils.get_object_url(existing);
                          has_image python: 'image' in df and utils.has_image(existing);">
     <h3><a href="${url}">${existing/Title}</a></h3>
    </tal:wrap>


Finally, define the ZCML to register it::

    <adapter
      name="existing.myview"
      provides="castle.cms.interfaces.ITileView"
      for="plone.dexterity.interfaces.IDexterityContent castle.cms.interfaces.ICastleLayer"
      factory=".myview.MyTileView"
      />


Lead images
-----------

- all content has lead images
- lead images can be references to other images on the site or to other content
  on the site that has a lead image


After the Deadline Spellchecking
--------------------------------

CastleCMS includes Plone's TinyMCE support for After the Deadline spellchecking and::

  - supports After the Deadline in rich text tiles
  - integrates spelling/grammar check within the content quality check dialog

To use After the Deadline, go to Site Setup and configure After the Deadline in the
TinyMCE configuration panel.
