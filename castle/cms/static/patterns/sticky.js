/* global define */

define([
  'jquery',
  'pat-base',
  'jquery.cookie'
], function($, Base) {
  'use strict';

  var StickyFooter = Base.extend({
    name: 'sticky',
    trigger: '.pat-sticky',
    parser: 'mockup',
    defaults: {},
    init: function() {
      var self = this;
      window.addEventListener("load", function(event) {
        if ($.cookie("sticky-footer") !== "footer-shown") {
          var stickyElement = $(".sticky-footer")
          stickyElement.show();
          stickyElement
            .css({ bottom: "-100px" })
            .animate({ bottom: "0px" }, "slow");
          self.setCookie("footer-shown");
        }
      });
    },

    setCookie: function(value) {
      return $.cookie("sticky-footer", value, { path: '/' });
    },
  });
  return StickyFooter;
});
