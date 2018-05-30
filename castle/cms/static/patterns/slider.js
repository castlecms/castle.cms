define([
  'jquery',
  'pat-base',
  'castle-url/libs/FlexSlider/jquery.flexslider'
], function($, Base) {
  "use strict";

  var Slider = Base.extend({
    name: 'slider',
    trigger: '.pat-slider',
    parser: 'mockup',
    defaults: {
      animation: 'fade',
      controlNav: true,
      directionNav: true,
      slideshowSpeed: 7000,
      animationSpeed: 600
    },
    init: function() {
      var self = this;
      self.$el.flexslider();
    }
  });

  return Slider;

});
