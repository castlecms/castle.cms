require([
    'castle-url/patterns/structure/pattern',
    'pat-registry'
  ], function(
     Structure,
     registry
    ) {
    'use strict';

    // unregister existing pattern
    delete registry.patterns.structure;
    delete $.fn.patStructure;

   return Structure;
  });