/* global define */

define([
  'jquery',
  'pat-base',
  'castle-url/libs/camera/scripts/jquery.easing.1.3',
  'castle-url/libs/camera/scripts/camera'
], function($, Base) {
  'use strict';

  var Gallery = Base.extend({
    name: 'gallery',
    trigger: '.pat-gallery',
    parser: 'mockup',
    defaults: {
      pagination: false,
      thumbnails: true
    },
    init: function() {
      var self = this;
      self.$el.camera(self.options);
    }
  });
  return Gallery;

});
