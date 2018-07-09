/* global define */

define([
  'jquery',
  'pat-base',
  'underscore',
  'castle-url/libs/mediaelement/build/mediaelement-and-player'
], function($, Base, _) {
  'use strict';

  var AudioPattern = Base.extend({
    name: 'audio',
    trigger: '.pat-audio',
    defaults: {
    },
    parser: 'mockup',
    init: function() {
      var self = this;
      self.$el.mediaelementplayer({});
    }
  });

  return AudioPattern;

});
