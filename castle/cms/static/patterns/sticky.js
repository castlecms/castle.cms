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
        self.cookie_data = $.cookie("sticky-footer");

        // Sets the cookie to indicate the footer was closed and won't re-appear.
        $(".close-footer").click(function() {
          self.cookie_data = self.setCookie("closed-footer")
        });

        if (self.cookie_data !== "closed-footer") {
          $(".sticky-footer").show();
            // If cookie hasn't been set yet, do the rising animation.
            if (typeof(self.cookie_data) === "undefined") {
              $(".sticky-footer")
                .css({ bottom: "-100px" })
                .animate({ bottom: "0px" }, "slow");
              self.cookie_data = self.setCookie("no-animation");
          }
      }
      });
    },

    setCookie: function(value) {
      return $.cookie("sticky-footer", value, { path: '/' });
    },
  });
  return StickyFooter;
});
