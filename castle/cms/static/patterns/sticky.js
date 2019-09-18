/* global define */

define([
  'jquery',
  'pat-base',
], function($, Base) {
  'use strict';

  var StickyFooter = Base.extend({
    name: 'sticky',
    trigger: '.pat-sticky',
    parser: 'mockup',
    defaults: {},
    init: function() {
      window.addEventListener("load", event => {
        debugger;
        $(".sticky-footer").show();
        $(".sticky-footer")
          .css({ bottom: "-100px" })
          .animate({ bottom: "0px" }, "slow");
      });
    }
  });
  return StickyFooter;
});
