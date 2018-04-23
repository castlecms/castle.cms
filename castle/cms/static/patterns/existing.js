/* global define */

define([
  'jquery',
  'pat-base',
], function($, Base) {
  'use strict';

  var ExistingContent = Base.extend({
    name: 'existing',
    trigger: '.pat-existing',
    parser: 'mockup',
    defaults: {
    },
    init: function() {
      this.loadContent();
    },
    loadContent: function() {
      var that = this;
      $('.pat-existing').each(function() {
        var main_content = $(this).attr('content_url') + ' #main-content';
        $(this).load(main_content);
      });
      that.loaded = true;
    }
  });

  return ExistingContent;

});
